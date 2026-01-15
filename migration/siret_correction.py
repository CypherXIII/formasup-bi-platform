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


def generate_luhn_valid_candidates(siret: str, max_distance: int = 2) -> List[str]:
    """! @brief Generates all Luhn-valid SIRET candidates within a given Hamming distance.

    @param siret Invalid SIRET to correct.
    @param max_distance Maximum Hamming distance from the original (default: 2).
    @return List of Luhn-valid SIRET candidates sorted by Hamming distance.
    """
    if not siret or len(siret) != 14 or not siret.isdigit():
        return []

    candidates = []
    siret_list = list(siret)

    # Generate candidates at distance 1 (single digit changes)
    for pos in range(14):
        original_digit = siret_list[pos]
        for digit in "0123456789":
            if digit != original_digit:
                siret_list[pos] = digit
                candidate = "".join(siret_list)
                if is_valid_luhn(candidate):
                    candidates.append((1, candidate))
        siret_list[pos] = original_digit

    # Generate candidates at distance 2 (two digit changes) if needed
    if max_distance >= 2:
        for pos1 in range(14):
            original_digit1 = siret_list[pos1]
            for digit1 in "0123456789":
                if digit1 != original_digit1:
                    siret_list[pos1] = digit1
                    for pos2 in range(pos1 + 1, 14):
                        original_digit2 = siret_list[pos2]
                        for digit2 in "0123456789":
                            if digit2 != original_digit2:
                                siret_list[pos2] = digit2
                                candidate = "".join(siret_list)
                                if is_valid_luhn(candidate):
                                    candidates.append((2, candidate))
                        siret_list[pos2] = original_digit2
            siret_list[pos1] = original_digit

    # Sort by distance, then by candidate value
    candidates.sort(key=lambda x: (x[0], x[1]))

    # Return only the SIRET strings, removing duplicates while preserving order
    seen = set()
    result = []
    for _, candidate in candidates:
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
            # First try to get city from company table directly if it has city_id
            ma_execute(cur, """
                SELECT c.name
                FROM company co
                JOIN city c ON co.city_id = c.id
                WHERE co.siret = %s
            """, (siret,))
            result = cur.fetchone()

            if result and result[0]:
                return result[0]

            # If not found, try to get city from registration -> host company
            ma_execute(cur, """
                SELECT DISTINCT c.name
                FROM registration r
                JOIN company co ON r.host_company_id = co.id
                JOIN city c ON co.city_id = c.id
                WHERE co.siret = %s
                LIMIT 1
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

    @param conn_maria Active MariaDB connection.
    @param siret SIRET to search for.
    @return Dictionary with company information (name, city_code, city_name, postal_code).
    """
    logger = logging.getLogger("migration")

    try:
        with conn_maria.cursor() as cur:
            # Get company info including city
            ma_execute(cur, """
                SELECT co.name, co.postal_code, c.name as city_name, c.code as city_code
                FROM company co
                LEFT JOIN city c ON co.city_id = c.id
                WHERE co.siret = %s
            """, (siret,))
            result = cur.fetchone()

            if result:
                return {
                    "name": result[0],
                    "postal_code": result[1],
                    "city_name": result[2],
                    "city_code": result[3]
                }

            return {}

    except Exception as e:
        logger.debug(f"Error retrieving company info for SIRET {siret}: {e}")
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


def validate_siret_with_api(
    siret: str,
    expected_city: Optional[str],
    api_client: RateLimitedAPI
) -> Optional[Dict[str, Any]]:
    """! @brief Validates a SIRET candidate against the French government API.

    @param siret SIRET candidate to validate.
    @param expected_city Expected city name for filtering (optional).
    @param api_client API client with rate limiting.
    @return Company data if SIRET is valid and matches city, None otherwise.
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

        company_city = etablissement.get("commune", "")

        # If expected city is provided, check if it matches (case-insensitive, partial match)
        if expected_city:
            expected_normalized = expected_city.upper().strip()
            actual_normalized = (company_city or "").upper().strip()

            # Allow partial match (city name might be shortened or have variations)
            if not (expected_normalized in actual_normalized or
                    actual_normalized in expected_normalized or
                    _normalize_city_name(expected_normalized) == _normalize_city_name(actual_normalized)):
                logger.debug(
                    f"SIRET {siret} city mismatch: expected '{expected_city}', got '{company_city}'"
                )
                return None

        return {
            "siret": siret,
            "name": result.get("nom_raison_sociale") or result.get("nom_complet"),
            "city": company_city,
            "code_naf": result.get("activite_principale"),
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
    max_distance: int = 2
) -> Optional[Dict[str, Any]]:
    """! @brief Attempts to correct an invalid SIRET using Hamming distance and API validation.

    @param invalid_siret The invalid SIRET to correct.
    @param conn_maria Active MariaDB connection.
    @param api_client API client with rate limiting.
    @param max_distance Maximum Hamming distance for candidates (default: 2).
    @return Dictionary with correction info if found, None otherwise.
    """
    logger = logging.getLogger("migration")
    logger.info(f"Attempting to correct invalid SIRET: {invalid_siret}")

    # Get company info from MariaDB (including city)
    company_info = get_company_info_from_mariadb(conn_maria, invalid_siret)
    city_name = company_info.get("city_name")
    company_name = company_info.get("name")
    postal_code = company_info.get("postal_code")

    logger.info(
        f"MariaDB info for {invalid_siret}: name='{company_name}', "
        f"city='{city_name}', postal_code='{postal_code}'"
    )

    # Strategy 1: Generate Luhn-valid candidates and validate with API + city filter
    candidates = generate_luhn_valid_candidates(invalid_siret, max_distance)
    logger.info(f"Generated {len(candidates)} Luhn-valid candidates for {invalid_siret}")

    # Test candidates (prioritize distance 1, then distance 2)
    for candidate in candidates[:100]:  # Limit to first 100 to avoid too many API calls
        result = validate_siret_with_api(candidate, city_name, api_client)
        if result:
            distance = hamming_distance(invalid_siret, candidate)
            logger.info(
                f"Found valid correction for {invalid_siret}: {candidate} "
                f"(distance={distance}, city='{result.get('city')}')"
            )
            return {
                "original_siret": invalid_siret,
                "corrected_siret": candidate,
                "hamming_distance": distance,
                "company_name": result.get("name"),
                "city": result.get("city"),
                "method": "hamming_distance"
            }

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
        f.write("=" * 50 + "\n\n")

        if corrections:
            f.write("SUCCESSFUL CORRECTIONS:\n")
            f.write("-" * 30 + "\n")
            for corr in corrections:
                f.write(f"Original:  {corr['original_siret']}\n")
                f.write(f"Corrected: {corr['corrected_siret']}\n")
                f.write(f"Distance:  {corr['hamming_distance']}\n")
                f.write(f"Company:   {corr.get('company_name', 'N/A')}\n")
                f.write(f"City:      {corr.get('city', 'N/A')}\n")
                f.write(f"Method:    {corr['method']}\n")
                f.write("\n")

        if uncorrected:
            f.write("\nUNCORRECTED SIRETS:\n")
            f.write("-" * 30 + "\n")
            for siret in uncorrected:
                f.write(f"{siret}\n")

        f.write("\n" + "=" * 50 + "\n")
        f.write(f"Total: {len(corrections)} corrected, {len(uncorrected)} uncorrected\n")
