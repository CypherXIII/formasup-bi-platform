#!/usr/bin/env python3
"""! @file siret_correction.py
@brief SIRET correction using Hamming distance and API validation.
@author Marie Challet
@organization Formasup Auvergne

This module provides functions to correct invalid SIRETs by:
1. Using Hamming distance to generate candidate corrections
2. Filtering candidates by city from the original MariaDB data
3. Validating candidates against the French government API
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

import psycopg2  # type: ignore
import pymysql  # type: ignore

from api_client import RateLimitedAPI
from config import Config
from database import ma_execute


def is_valid_luhn(number: str) -> bool:
    """! @brief Checks if a number complies with the Luhn algorithm (modulo 10).
    @param number String representing the number to check.
    @return True if the number is valid according to the Luhn algorithm, False otherwise.
    """
    if not number or not number.isdigit():
        return False

    digits = [int(d) for d in number]

    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9

    return sum(digits) % 10 == 0


def hamming_distance(s1: str, s2: str) -> int:
    """! @brief Calculates the Hamming distance between two strings of equal length.
    @param s1 First string.
    @param s2 Second string.
    @return Number of positions where the characters differ.
    @raises ValueError If strings have different lengths.
    """
    if len(s1) != len(s2):
        raise ValueError("Strings must have equal length for Hamming distance")
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))


def generate_luhn_valid_candidates(siret: str, max_distance: int = 1) -> List[str]:
    """! @brief Generates all Luhn-valid SIRET candidates within a given Hamming distance.

    Optimized for distance=1 only (fastest option, ~140 candidates per SIRET).

    @param siret Invalid SIRET to correct.
    @param max_distance Maximum Hamming distance from the original (default: 1, max: 1).
    @return List of Luhn-valid SIRET candidates.
    """
    if not siret or len(siret) != 14 or not siret.isdigit():
        return []

    candidates = []
    siret_list = list(siret)

    # Generate candidates at distance 1 (single digit changes)
    # ~14 * 9 = ~126 candidates per SIRET (fast!)
    for pos in range(14):
        original_digit = siret_list[pos]
        for digit in "0123456789":
            if digit != original_digit:
                siret_list[pos] = digit
                candidate = "".join(siret_list)
                if is_valid_luhn(candidate):
                    candidates.append(candidate)
        siret_list[pos] = original_digit

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            result.append(candidate)

    return result


def get_company_city_from_mariadb(
    conn_maria: pymysql.connections.Connection,
    siret: str
) -> Optional[str]:
    """! @brief Retrieves the city name associated with a company SIRET from MariaDB.

    @param conn_maria Active MariaDB connection.
    @param siret SIRET to search for.
    @return City name or None if not found.
    """
    logger = logging.getLogger("migration")

    try:
        with conn_maria.cursor() as cur:
            # Get city from company table using address_city_id
            ma_execute(cur, """
                SELECT c.name
                FROM company co
                JOIN city c ON co.address_city_id = c.id
                WHERE co.siret = %s
                AND co.discr LIKE 'company_official%%'
            """, (siret,))
            result = cur.fetchone()

            if result and result[0]:
                return result[0]

            return None

    except Exception as e:
        logger.debug(f"Error retrieving city for SIRET {siret}: {e}")
        return None


def get_company_info_from_mariadb(
    conn_maria: pymysql.connections.Connection,
    siret: str
) -> Dict[str, Any]:
    """! @brief Retrieves company information from MariaDB for a given SIRET.

    Tries multiple query strategies to find the data.

    @param conn_maria Active MariaDB connection.
    @param siret SIRET to search for.
    @return Dictionary with company information (name, city_code, city_name).
    """
    logger = logging.getLogger("migration")

    if not conn_maria:
        logger.error("MariaDB connection is None!")
        return {}

    try:
        with conn_maria.cursor() as cur:
            # Strategy 1: Try with company_official discriminator (preferred)
            # Using exact query structure that works: SELECT company.siret, city.code, company.name, city.name
            query1 = """
                SELECT company.name, city.code, city.name as city_name
                FROM company
                LEFT JOIN city ON company.address_city_id = city.id
                WHERE company.siret = %s
                AND company.discr LIKE 'company_official%%'
            """
            logger.debug(f"Executing query 1 for SIRET {siret}")
            ma_execute(cur, query1, (siret,))
            result = cur.fetchone()
            logger.debug(f"Query 1 result for {siret}: {result}")

            # Strategy 2: Try without discriminator filter (fallback)
            if not result or not result[0]:
                query2 = """
                    SELECT company.name, city.code, city.name as city_name
                    FROM company
                    LEFT JOIN city ON company.address_city_id = city.id
                    WHERE company.siret = %s
                """
                logger.debug(f"Executing query 2 (fallback) for SIRET {siret}")
                ma_execute(cur, query2, (siret,))
                result = cur.fetchone()
                logger.debug(f"Query 2 result for {siret}: {result}")

            if result and result[0]:
                return {
                    "name": result[0],
                    "city_code": result[1],
                    "city_name": result[2]
                }

            logger.warning(f"No company info found for SIRET {siret}")
            return {}

    except Exception as e:
        logger.error(f"Error retrieving company info for SIRET {siret}: {e}", exc_info=True)
        return {}


def search_company_by_name_and_city(
    name: str,
    city: str,
    postal_code: Optional[str],
    api_client: RateLimitedAPI
) -> List[Dict[str, Any]]:
    """! @brief Searches for companies by name and city using the French government API.

    @param name Company name to search for.
    @param city City name.
    @param postal_code Optional postal code for filtering.
    @param api_client API client with rate limiting.
    @return List of matching companies with their SIRETs.
    """
    logger = logging.getLogger("migration")

    # Build search query with company name and city
    search_terms = []
    if name:
        search_terms.append(name)
    if city:
        search_terms.append(city)

    if not search_terms:
        return []

    query = " ".join(search_terms)

    url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {
        "q": query,
        "per_page": 25,
        "include": "matching_etablissements, siege"
    }

    # Add postal code filter if available
    if postal_code and len(postal_code) >= 2:
        params["departement"] = postal_code[:2]

    try:
        response = api_client.request(
            "GET", url, params=params, headers={"Accept": "application/json"}
        )

        if response is None or response.status_code != 200:
            return []

        data = response.json()
        results = []

        for company in data.get("results", []):
            # Get all etablissements
            etablissements = company.get("matching_etablissements", [])
            siege = company.get("siege", {})

            # Add siege if it has a SIRET
            if siege.get("siret"):
                results.append({
                    "siret": siege["siret"],
                    "name": company.get("nom_raison_sociale") or company.get("nom_complet"),
                    "city": siege.get("commune"),
                    "postal_code": siege.get("code_postal"),
                    "is_siege": True
                })

            # Add all matching etablissements
            for etab in etablissements:
                if etab.get("siret") and etab.get("siret") != siege.get("siret"):
                    results.append({
                        "siret": etab["siret"],
                        "name": company.get("nom_raison_sociale") or company.get("nom_complet"),
                        "city": etab.get("commune"),
                        "postal_code": etab.get("code_postal"),
                        "is_siege": False
                    })

        return results

    except Exception as e:
        logger.debug(f"Error searching companies: {e}")
        return []


def _normalize_company_name(name: str) -> str:
    """! @brief Normalizes a company name for comparison.

    Removes common legal forms and standardizes formatting.

    @param name Company name to normalize.
    @return Normalized company name.
    """
    if not name:
        return ""

    import re
    normalized = name.upper().strip()

    # Remove common legal forms
    legal_forms = [
        r'\bSAS\b', r'\bSARU\b', r'\bSARL\b', r'\bSA\b', r'\bEURL\b',
        r'\bSCI\b', r'\bSNC\b', r'\bSELARL\b', r'\bSCP\b',
        r'\bASSOCIATION\b', r'\bASSOC\b', r'\bETABLISSEMENT\b',
        r'\bENTREPRISE\b', r'\bSOCIETE\b', r'\bGROUPE\b',
    ]
    for form in legal_forms:
        normalized = re.sub(form, '', normalized)

    # Remove punctuation and extra spaces
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = ' '.join(normalized.split())

    return normalized


def validate_siret_with_api(
    siret: str,
    expected_name: Optional[str],
    expected_city_code: Optional[str],
    api_client: RateLimitedAPI
) -> Optional[Dict[str, Any]]:
    """! @brief Validates a SIRET candidate against the French government API.

    @param siret SIRET candidate to validate.
    @param expected_name Expected company name for filtering (optional).
    @param expected_city_code Expected city INSEE code for filtering (optional).
    @param api_client API client with rate limiting.
    @return Company data if SIRET exists, None otherwise.
    """
    logger = logging.getLogger("migration")

    url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {
        "q": siret,
        "minimal": "true",
        "include": "matching_etablissements, siege"
    }

    try:
        response = api_client.request(
            "GET", url, params=params, headers={"Accept": "application/json"}
        )

        if response is None or response.status_code != 200:
            return None

        data = response.json()
        if not data.get("results"):
            return None

        result = data["results"][0]
        etablissement = result.get("matching_etablissements", [{}])[0]

        # Filter out closed establishments
        etat = etablissement.get("etat_administratif", "")
        if etat and etat.lower() in ["f", "fermé", "closed", "ferme"]:
            logger.debug(f"SIRET {siret} is closed (etat_administratif: {etat})")
            return None

        # Get city info from API
        # API field mapping:
        #   - commune = INSEE code (e.g., "63338")
        #   - libelle_commune = city name (e.g., "SAINT-ELOY-LES-MINES")
        api_city_code = etablissement.get("commune", "")  # INSEE code
        api_city_name = etablissement.get("libelle_commune", "")  # City name

        # Get company name
        api_name = result.get("nom_raison_sociale") or result.get("nom_complet")

        # Calculate match scores for ranking
        name_match_score = 0
        city_match_score = 0

        # Check name match
        if expected_name and api_name:
            expected_normalized = _normalize_company_name(expected_name)
            actual_normalized = _normalize_company_name(api_name)

            if expected_normalized and actual_normalized:
                expected_words = set(expected_normalized.split())
                actual_words = set(actual_normalized.split())
                common_words = expected_words & actual_words
                significant_common = [w for w in common_words if len(w) > 2]
                name_match_score = len(significant_common)

        # Check city match using INSEE code
        if expected_city_code and api_city_code:
            if expected_city_code == api_city_code:
                city_match_score = 2  # Exact INSEE code match

        return {
            "siret": siret,
            "name": api_name,
            "city": api_city_name,
            "city_code": api_city_code,
            "expected_name": expected_name,
            "expected_city_code": expected_city_code,
            "code_naf": result.get("activite_principale"),
            "name_match_score": name_match_score,
            "city_match_score": city_match_score,
            "is_valid": True
        }

    except Exception as e:
        logger.debug(f"Error validating SIRET {siret}: {e}")
        return None


def _normalize_city_name(name: str) -> str:
    """! @brief Normalizes a city name for comparison.

    Removes common prefixes, suffixes, and standardizes formatting.

    @param name City name to normalize.
    @return Normalized city name.
    """
    if not name:
        return ""

    normalized = name.upper().strip()

    # Remove common prefixes
    prefixes = ["SAINT-", "SAINT ", "ST-", "ST ", "SAINTE-", "SAINTE "]
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = "ST" + normalized[len(prefix):]
            break

    # Remove common suffixes like district numbers
    import re
    normalized = re.sub(r'\s+\d+E?\s*$', '', normalized)
    normalized = re.sub(r'\s+CEDEX.*$', '', normalized)

    # Remove dashes and extra spaces
    normalized = normalized.replace("-", " ")
    normalized = " ".join(normalized.split())

    return normalized


def correct_invalid_siret(
    invalid_siret: str,
    conn_maria: pymysql.connections.Connection,
    api_client: RateLimitedAPI,
    max_distance: int = 1,
    max_candidates: int = 5
) -> Optional[Dict[str, Any]]:
    """! @brief Attempts to correct an invalid SIRET using Hamming distance and API validation.

    Returns multiple correction candidates ranked by match quality.
    Uses parallel API requests for speed.

    @param invalid_siret The invalid SIRET to correct.
    @param conn_maria Active MariaDB connection.
    @param api_client API client with rate limiting.
    @param max_distance Maximum Hamming distance for candidates (default: 1 for speed).
    @param max_candidates Maximum number of candidates to return (default: 5).
    @return Dictionary with correction info and all candidates, None if none found.
    """
    logger = logging.getLogger("migration")
    logger.info(f"Attempting to correct invalid SIRET: {invalid_siret}")

    # Get company info from MariaDB (including city INSEE code and name)
    if not conn_maria:
        logger.error(f"MariaDB connection is None for SIRET {invalid_siret}!")
        return None

    company_info = get_company_info_from_mariadb(conn_maria, invalid_siret)
    logger.debug(f"Complete company_info dict for {invalid_siret}: {company_info}")

    city_code = company_info.get("city_code")  # INSEE code
    city_name = company_info.get("city_name")
    company_name = company_info.get("name")
    postal_code = company_info.get("postal_code")

    logger.info(
        f"MariaDB info for {invalid_siret}: name='{company_name}', "
        f"city='{city_name}' (INSEE: {city_code}), postal_code='{postal_code}'"
    )

    # Strategy 1: Generate Luhn-valid candidates and validate with API in parallel
    candidates = generate_luhn_valid_candidates(invalid_siret, max_distance)
    logger.info(f"Generated {len(candidates)} Luhn-valid candidates for {invalid_siret}")

    # Test candidates in parallel using ThreadPoolExecutor
    valid_candidates = []

    def validate_candidate(candidate: str) -> Optional[Dict[str, Any]]:
        """Validate a single candidate and return extended info if valid."""
        result = validate_siret_with_api(candidate, company_name, city_code, api_client)
        if result:
            try:
                distance = hamming_distance(invalid_siret, candidate)
            except ValueError:
                return None

            return {
                "original_siret": invalid_siret,
                "corrected_siret": candidate,
                "hamming_distance": distance,
                "company_name": result.get("name"),
                "expected_name": company_name,
                "city": result.get("city"),
                "city_code": result.get("city_code"),
                "expected_city": city_name,
                "expected_city_code": city_code,
                "name_match_score": result.get("name_match_score", 0),
                "city_match_score": result.get("city_match_score", 0),
                "method": "hamming_distance"
            }
        return None

    # Use ThreadPoolExecutor for parallel API requests (4 threads, safe with rate limiting)
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all candidates
        future_to_candidate = {
            executor.submit(validate_candidate, cand): cand
            for cand in candidates[:max_candidates * 5]  # Check 5x more candidates in parallel
        }

        # Collect results as they complete
        for future in as_completed(future_to_candidate):
            try:
                result = future.result()
                if result:
                    valid_candidates.append(result)

                    # Stop early if we have enough good matches
                    if len(valid_candidates) >= max_candidates:
                        break
            except Exception as e:
                logger.debug(f"Error validating SIRET candidate: {e}")
                continue

    # If we have candidates, rank them and return all
    if valid_candidates:
        # Sort by: match score (name + city), then distance, then SIRET
        valid_candidates.sort(
            key=lambda x: (
                -(x["name_match_score"] + x["city_match_score"]),  # Higher score first
                x["hamming_distance"],  # Lower distance first
                x["corrected_siret"]  # Deterministic
            )
        )

        best = valid_candidates[0]
        all_sirets = [c["corrected_siret"] for c in valid_candidates]

        logger.info(
            f"Found {len(valid_candidates)} correction(s) for {invalid_siret}: "
            f"best={best['corrected_siret']} (distance={best['hamming_distance']}, "
            f"name='{best.get('company_name')}', city='{best.get('city')}')"
        )

        # Return best candidate with all alternatives
        best["all_candidates"] = valid_candidates
        best["needs_manual_review"] = len(valid_candidates) > 1

        return best

    # Strategy 2: Search by company name and city if Hamming approach fails
    if company_name and city_name:
        logger.info(f"Trying API search by name and city for {invalid_siret}")
        search_results = search_company_by_name_and_city(
            company_name, city_name, postal_code, api_client
        )

        for result in search_results:
            candidate_siret = result.get("siret")
            if candidate_siret and is_valid_luhn(candidate_siret):
                # Calculate distance to see if it's close to original
                try:
                    if len(candidate_siret) == 14:
                        distance = hamming_distance(invalid_siret, candidate_siret)
                        if distance <= max_distance + 2:  # Allow slightly larger distance for name search
                            logger.info(
                                f"Found correction via name search for {invalid_siret}: {candidate_siret} "
                                f"(distance={distance}, name='{result.get('name')}')"
                            )
                            return {
                                "original_siret": invalid_siret,
                                "corrected_siret": candidate_siret,
                                "hamming_distance": distance,
                                "company_name": result.get("name"),
                                "city": result.get("city"),
                                "method": "name_city_search"
                            }
                except ValueError:
                    continue

    logger.warning(f"No valid correction found for SIRET {invalid_siret}")
    return None


def correct_invalid_sirets_batch(
    invalid_sirets: List[str],
    conn_maria: pymysql.connections.Connection,
    api_client: RateLimitedAPI,
    max_distance: int = 2
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """! @brief Attempts to correct a batch of invalid SIRETs.

    @param invalid_sirets List of invalid SIRETs to correct.
    @param conn_maria Active MariaDB connection.
    @param api_client API client with rate limiting.
    @param max_distance Maximum Hamming distance for candidates.
    @return Tuple of (list of corrections, list of uncorrected SIRETs).
    """
    logger = logging.getLogger("migration")
    logger.info(f"=== Correcting {len(invalid_sirets)} invalid SIRETs ===")

    corrections = []
    uncorrected = []

    for i, siret in enumerate(invalid_sirets):
        logger.info(f"Processing {i + 1}/{len(invalid_sirets)}: {siret}")

        result = correct_invalid_siret(siret, conn_maria, api_client, max_distance)

        if result:
            corrections.append(result)
        else:
            uncorrected.append(siret)

    # Log summary
    logger.info("=== SIRET Correction Summary ===")
    logger.info(f"Total processed: {len(invalid_sirets)}")
    logger.info(f"Corrected: {len(corrections)}")
    logger.info(f"Uncorrected: {len(uncorrected)}")

    if corrections:
        logger.info("Corrections found:")
        for corr in corrections:
            logger.info(
                f"  {corr['original_siret']} -> {corr['corrected_siret']} "
                f"(distance={corr['hamming_distance']}, method={corr['method']})"
            )

    if uncorrected:
        logger.info(f"Uncorrected SIRETs: {', '.join(uncorrected)}")

    return corrections, uncorrected


def write_correction_report(
    corrections: List[Dict[str, Any]],
    uncorrected: List[str],
    output_file: str = "siret_corrections.txt"
) -> None:
    """! @brief Writes a correction report to a file.

    @param corrections List of successful corrections.
    @param uncorrected List of uncorrected SIRETs.
    @param output_file Output file path.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("SIRET Correction Report\n")
        f.write("=" * 70 + "\n\n")

        if corrections:
            f.write("CORRECTION SUGGESTIONS:\n")
            f.write("-" * 70 + "\n\n")

            for corr in corrections:
                f.write(f"ORIGINAL SIRET: {corr['original_siret']}\n")
                f.write(f"Expected (MariaDB): name='{corr.get('expected_name', 'N/A')}', ")
                f.write(f"city='{corr.get('expected_city', 'N/A')}' ")
                f.write(f"(INSEE: {corr.get('expected_city_code', 'N/A')})\n")
                f.write("-" * 40 + "\n")

                # Show all candidates
                all_candidates = corr.get("all_candidates", [corr])
                f.write(f"Found {len(all_candidates)} candidate(s):\n\n")

                for i, cand in enumerate(all_candidates, 1):
                    # Mark best match
                    is_best = (i == 1)
                    marker = " [BEST MATCH]" if is_best else ""

                    city_name_display = cand.get('city', '') or 'N/A'
                    city_code_display = cand.get('city_code', '') or 'N/A'

                    f.write(f"  {i}. SIRET: {cand['corrected_siret']}{marker}\n")
                    f.write(f"     Company: {cand.get('company_name', 'N/A')}\n")
                    f.write(f"     City:    {city_name_display} (INSEE: {city_code_display})\n")
                    f.write(f"     Distance: {cand['hamming_distance']} digit(s)\n")

                    # Show match scores
                    name_score = cand.get("name_match_score", 0)
                    city_score = cand.get("city_match_score", 0)
                    if name_score > 0 or city_score > 0:
                        f.write(f"     Match: name={name_score}, city={city_score}\n")
                    f.write("\n")

                if corr.get("needs_manual_review"):
                    f.write("  *** MANUAL REVIEW RECOMMENDED ***\n")

                f.write("\n" + "=" * 70 + "\n\n")

        if uncorrected:
            f.write("UNCORRECTED SIRETS (no valid candidate found):\n")
            f.write("-" * 40 + "\n")
            for siret in uncorrected:
                f.write(f"  {siret}\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write(f"SUMMARY: {len(corrections)} with suggestions, {len(uncorrected)} without\n")
