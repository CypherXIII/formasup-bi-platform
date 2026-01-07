#!/usr/bin/env python3
"""! @file api_enrichment.py
@brief Functions for enriching data via external APIs.
@author Marie Challet
@organization Formasup Auvergne

This module provides functionalities to enrich company data using French government APIs.
It includes SIRET validation, company data retrieval, and OPCO enrichment.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import psycopg2

from api_client import RateLimitedAPI
from database import transaction
from config import Config


def is_valid_luhn(number: str) -> bool:
    """! @brief Checks if a number complies with the Luhn algorithm (modulo 10).
    @param number String representing the number to check.
    @return True if the number is valid according to the Luhn algorithm, False otherwise.
    """
    if not number or not number.isdigit():
        return False

    # Convert to a list of integers
    digits = [int(d) for d in number]

    # Apply the Luhn algorithm
    # Start from the second to last digit, go left, in steps of 2
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9

    # Check if the sum is divisible by 10
    return sum(digits) % 10 == 0


def is_valid_siret(siret: str) -> bool:
    """! @brief Checks if a SIRET is valid (length and validation algorithms).
    @param siret String representing the SIRET to check.
    @return True if the SIRET is valid, False otherwise.
    @note General case: Luhn algorithm check.
    @note La Poste special case: If Luhn fails, check that the sum of the digits is a multiple of 5 (for SIRETs starting with 35600).
    """
    if not siret or len(siret) != 14 or not siret.isdigit():
        return False

    # Standard check with the Luhn algorithm
    if is_valid_luhn(siret):
        return True

    # La Poste special case (SIREN 356000000 = SIRET starting with 35600)
    # If the Luhn algorithm fails, check the special La Poste rule
    if siret.startswith("35600"):
        # For La Poste, the sum of all digits must be a multiple of 5
        digit_sum = sum(int(digit) for digit in siret)
        if digit_sum % 5 == 0:
            return True

    return False


def get_api_company_data(siret: str, api_client: RateLimitedAPI) -> Dict[str, Any]:
    """! @brief Retrieves company data via the government API.
    @param siret SIRET number of the company to search.
    @param api_client API client with rate limiting.
    @return Dictionary containing company information or an empty dict in case of an error.
    """
    logger = logging.getLogger("migration")

    # SIRET validation with appropriate algorithms
    if not is_valid_siret(siret):
        logger.warning(f"Invalid SIRET (format, Luhn or special rule): {siret}")
        return {}

    url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {
        "q": siret,
        "minimal": "true",
        "include": "matching_etablissements, siege",
    }

    try:
        response = api_client.request(
            "GET", url, params=params, headers={"Accept": "application/json"}
        )

        if response is None or response.status_code != 200:
            logger.warning(
                f"API error for SIRET {siret}: {response and response.status_code}"
            )
            return {}

        data = response.json()
        if not data.get("results"):
            logger.warning(f"No data found for SIRET {siret}")
            return {}

        result = data["results"][0]
        etablissement = result.get("matching_etablissements", [{}])[0]

        return {
            "name": result.get("nom_raison_sociale") or result.get("nom_complet"),
            "code_naf": result.get("activite_principale"),
            "idcc": ", ".join(etablissement.get("liste_idcc", []))
            if etablissement.get("liste_idcc")
            else None,
            "commune": etablissement.get("commune"),
            "workforce_range": result.get("tranche_effectif_salarie"),
            "category": result.get("categorie_entreprise"),
            "type": result.get("nature_juridique")[:2]
            if result.get("nature_juridique")
            else None,
        }

    except Exception as e:
        logger.error(f"API Exception for SIRET {siret}: {e}")
        return {}


def get_api_company_data_siege(
    siren: str, api_client: RateLimitedAPI
) -> Dict[str, Any]:
    """! @brief Retrieves head office data for a company via the government API.
    @param siren SIREN number of the company.
    @param api_client API client with rate limiting.
    @return Dictionary containing head office information or an empty dict in case of an error.
    """
    logger = logging.getLogger("migration")

    url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {"q": siren, "minimal": "true", "include": "siege"}

    try:
        response = api_client.request(
            "GET", url, params=params, headers={"Accept": "application/json"}
        )

        if response is None or response.status_code != 200:
            logger.warning(
                f"API error for SIREN {siren}: {response and response.status_code}"
            )
            return {}

        data = response.json()
        if not data.get("results"):
            logger.warning(f"No data found for SIREN {siren}")
            return {}

        result = data["results"][0]
        siege = result.get("siege", {})

        return {
            "name": result.get("nom_raison_sociale") or result.get("nom_complet"),
            "code_naf": result.get("activite_principale"),
            "idcc": ", ".join(siege.get("liste_idcc", []))
            if siege.get("liste_idcc")
            else None,
            "commune": siege.get("commune"),
            "workforce_range": result.get("tranche_effectif_salarie"),
            "category": result.get("categorie_entreprise"),
            "type": result.get("nature_juridique")[:2]
            if result.get("nature_juridique")
            else None,
        }
    except Exception as e:
        logger.error(f"API Exception for SIREN {siren}: {e}")
        return {}


def find_idcc_id(
    conn_pg: psycopg2.extensions.connection, cfg: Config, idcc_code: str
) -> int:
    """! @brief Finds the ID of an IDCC in the idcc table from its code.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration with schema information.
    @param idcc_code IDCC code to search for.
    @return ID of the found IDCC or 0 if not found.
    """
    if not idcc_code:
        return 0

    try:
        with conn_pg.cursor() as cur:
            cur.execute(
                f"SELECT id FROM {cfg.pg_schema}.idcc WHERE code = %s LIMIT 1",
                (idcc_code,),
            )
            result = cur.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logging.getLogger("migration").error(
            f"Error while searching for IDCC {idcc_code}: {e}"
        )
        return 0


def find_city_id(
    conn_pg: psycopg2.extensions.connection, cfg: Config, commune: str
) -> int:
    """! @brief Finds the ID of a city in the city table from its code.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration with schema information.
    @param commune INSEE code of the commune to search for.
    @return ID of the found city or 0 if not found.
    """
    if not commune:
        return 0

    try:
        with conn_pg.cursor() as cur:
            cur.execute(
                f"SELECT id FROM {cfg.pg_schema}.city WHERE code = %s LIMIT 1",
                (commune,),
            )
            result = cur.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logging.getLogger("migration").error(
            f"Error while searching for city {commune}: {e}"
        )
        return 0


def find_naf_id(
    conn_pg: psycopg2.extensions.connection, cfg: Config, naf_code: str
) -> int:
    """! @brief Finds the ID of a NAF code in the naf_code table.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration with schema information.
    @param naf_code NAF code to search for.
    @return ID of the found NAF code or 0 if not found.
    """
    if not naf_code:
        return 0

    try:
        with conn_pg.cursor() as cur:
            cur.execute(
                f"SELECT id FROM {cfg.pg_schema}.naf WHERE code = %s LIMIT 1",
                (naf_code,),
            )
            result = cur.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logging.getLogger("migration").error(
            f"Error while searching for NAF code {naf_code}: {e}"
        )
        return 0


def find_type_id(
    conn_pg: psycopg2.extensions.connection, cfg: Config, type_code: str
) -> int:
    """! @brief Finds the ID of a company type in the company_type table.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration with schema information.
    @param type_code Company type code to search for.
    @return ID of the found company type or 0 if not found.
    """
    if not type_code:
        return 0

    try:
        with conn_pg.cursor() as cur:
            cur.execute(
                f"SELECT id FROM {cfg.pg_schema}.company_type WHERE code = %s LIMIT 1",
                (type_code,),
            )
            result = cur.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logging.getLogger("migration").error(
            f"Error while searching for type {type_code}: {e}"
        )
        return 0


def api_enrich_companies(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> Dict[str, int]:
    """! @brief Updates companies with data from the API.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration with schema information and API settings.
    @return Dictionary containing enrichment statistics (processed, inserted, errors, etc.).
    """
    logger = logging.getLogger("migration")
    logger.info("=== Company API Enrichment ===")

    if not cfg.api_enabled:
        logger.info("Company API enrichment disabled in configuration")
        return {"processed": 0, "inserted": 0, "errors": 0}

    stats = {
        "processed": 0,
        "inserted": 0,
        "errors": 0,
        "invalid_siret": 0,
        "laposte_valid": 0,
    }
    error_sirets = []
    invalid_sirets = []
    laposte_sirets = []

    # Create a reusable API client instance
    api_client = RateLimitedAPI(cfg.requests_per_second)

    try:
        # Retrieve SIRETs to process
        sirets = _get_sirets_to_process(conn_pg, cfg)
        if not sirets:
            logger.info("No SIRETs to process")
            return stats

        # Validate SIRETs before processing
        valid_sirets, invalid_sirets, laposte_sirets = _validate_sirets(sirets)

        # Update statistics
        stats["invalid_siret"] = len(invalid_sirets)
        stats["laposte_valid"] = len(laposte_sirets)

        logger.info(
            f"Total: {len(sirets)} SIRETs, Valid: {len(valid_sirets)}, Invalid: {len(invalid_sirets)}"
        )

        if laposte_sirets:
            logger.info(
                f"La Poste SIRETs validated by special rule: {len(laposte_sirets)} (e.g., {laposte_sirets[0] if laposte_sirets else 'N/A'})"
            )

        _log_invalid_sirets(invalid_sirets)

        if not valid_sirets:
            logger.info("No valid SIRETs to process")
            return stats

        # Process valid SIRETs
        for siret in valid_sirets:
            stats["processed"] += 1

            try:
                # Retrieve and process data for a SIRET
                if _process_single_siret(
                    conn_pg, cfg, siret, api_client, laposte_sirets
                ):
                    stats["inserted"] += 1
                else:
                    stats["errors"] += 1
                    error_sirets.append(siret)
            except Exception as e:
                logger.error(f"Error while processing SIRET {siret}: {e}")
                stats["errors"] += 1
                error_sirets.append(siret)

            # Progress log
            if stats["processed"] % 50 == 0:
                logger.info(
                    f"Progress: {stats['processed']}/{len(valid_sirets)} processed"
                )

    except Exception as e:
        logger.exception(f"Error during company enrichment: {e}")

    # Generate final report
    _generate_error_report(stats, invalid_sirets, error_sirets, laposte_sirets)

    logger.info("Company API enrichment finished")
    logger.info(
        f"Statistics: Processed: {stats['processed']}, Inserted: {stats['inserted']}, Errors: {stats['errors']}, La Poste: {stats['laposte_valid']}"
    )

    return stats


def _get_sirets_to_process(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> list:
    """! @brief Retrieves the list of SIRETs to process.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration with schema information.
    @return List of SIRETs to process.
    """
    logger = logging.getLogger("migration")

    try:
        with conn_pg.cursor() as cur:
            cur.execute(f"""
                SELECT DISTINCT c.siret 
                FROM {cfg.pg_schema}.company c
                WHERE c.siret IS NOT NULL 
                AND c.siret != ''
                AND c.siret NOT IN (
                    SELECT siret FROM {cfg.pg_schema}.company_info 
                    WHERE siret IS NOT NULL
                )
                LIMIT 1000
            """)
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error while retrieving SIRETs: {e}")
        return []


def _validate_sirets(sirets: list) -> tuple:
    """! @brief Validates SIRETs and separates them into categories.
    @param sirets List of SIRETs to validate.
    @return Tuple containing (valid sirets, invalid sirets, La Poste sirets).
    """
    valid_sirets = []
    invalid_sirets = []
    laposte_sirets = []

    for siret in sirets:
        if is_valid_siret(siret):
            valid_sirets.append(siret)
            # Identify La Poste SIRETs validated by special rule
            if siret.startswith("35600") and not is_valid_luhn(siret):
                laposte_sirets.append(siret)
        else:
            invalid_sirets.append(siret)

    return valid_sirets, invalid_sirets, laposte_sirets


def _log_invalid_sirets(invalid_sirets: list) -> None:
    """! @brief Logs information about invalid SIRETs.
    @param invalid_sirets List of invalid SIRETs.
    """
    logger = logging.getLogger("migration")

    if not invalid_sirets:
        return

    logger.warning(
        f"Invalid SIRETs: {', '.join(invalid_sirets[:10])}{'...' if len(invalid_sirets) > 10 else ''}"
    )

    # Analysis of error types
    format_errors = [s for s in invalid_sirets if len(s) != 14 or not s.isdigit()]
    luhn_errors = [
        s
        for s in invalid_sirets
        if len(s) == 14 and s.isdigit() and not s.startswith("35600")
    ]
    laposte_errors = [s for s in invalid_sirets if s.startswith("35600")]

    if format_errors:
        logger.warning(
            f"SIRETs with format errors: {len(format_errors)} (e.g., {format_errors[0] if format_errors else 'N/A'})"
        )
    if luhn_errors:
        logger.warning(
            f"SIRETs with Luhn errors: {len(luhn_errors)} (e.g., {luhn_errors[0] if luhn_errors else 'N/A'})"
        )
    if laposte_errors:
        logger.warning(
            f"Invalid La Poste SIRETs: {len(laposte_errors)} (e.g., {laposte_errors[0] if laposte_errors else 'N/A'})"
        )


def _process_single_siret(
    conn_pg: psycopg2.extensions.connection,
    cfg: Config,
    siret: str,
    api_client: RateLimitedAPI,
    laposte_sirets: list,
) -> bool:
    """! @brief Processes an individual SIRET.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration with schema information.
    @param siret SIRET to process.
    @param api_client API client with rate limiting.
    @param laposte_sirets List of La Poste SIRETs for categorization.
    @return True if processing was successful, False otherwise.
    """
    logger = logging.getLogger("migration")

    # Retrieve API data
    api_data = get_api_company_data(siret, api_client)
    if not api_data:
        logger.error(f"ERROR SIRET: {siret} - No data retrieved from API")
        return False

    try:
        # Retrieve the corresponding company ID
        with conn_pg.cursor() as cur:
            cur.execute(
                f"SELECT id FROM {cfg.pg_schema}.company WHERE siret = %s;",
                (siret,),
            )
            company_result = cur.fetchone()

            if not company_result:
                logger.warning(
                    f"No entry found in company for SIRET {siret}"
                )
                return False

            company_id = company_result[0]

        # Extract SIREN
        siren = siret[:9]

        # Retrieve necessary data
        idcc_id, first_idcc = _get_idcc_info(
            conn_pg, cfg, siret, siren, api_data, api_client
        )
        city_id = find_city_id(conn_pg, cfg, api_data.get("commune"))
        naf_id = find_naf_id(conn_pg, cfg, api_data.get("code_naf"))
        type_id = find_type_id(conn_pg, cfg, api_data.get("type"))
        workforce = _convert_workforce_range(api_data.get("workforce_range"))

        # Insert into company_info
        with transaction(conn_pg) as cur:
            cur.execute(
                f"""
                INSERT INTO {cfg.pg_schema}.company_info (
                    id, siret, name, naf_id, idcc_id, city_id, 
                    workforce, category, type_id, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (siret) DO UPDATE SET
                    name = EXCLUDED.name,
                    naf_id = EXCLUDED.naf_id,
                    idcc_id = EXCLUDED.idcc_id,
                    city_id = EXCLUDED.city_id,
                    workforce = EXCLUDED.workforce,
                    category = EXCLUDED.category,
                    type_id = EXCLUDED.type_id,
                    updated_at = NOW()
            """,
                (
                    company_id,
                    siret,
                    api_data.get("name"),
                    naf_id,
                    idcc_id,
                    city_id,
                    workforce,
                    api_data.get("category"),
                    type_id,
                ),
            )

        siret_type = "La Poste" if siret in laposte_sirets else "Standard"
        logger.info(f"Inserted ({siret_type}): {siret} - {api_data.get('name', 'N/A')}")
        return True

    except Exception as e:
        logger.error(f"Insertion error for {siret}: {e}")
        return False


def _get_idcc_info(
    conn_pg: psycopg2.extensions.connection,
    cfg: Config,
    siret: str,
    siren: str,
    api_data: Dict[str, Any],
    api_client: RateLimitedAPI,
) -> tuple:
    """! @brief Retrieves IDCC information for a company.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration with schema information.
    @param siret Company SIRET.
    @param siren Company SIREN.
    @param api_data API data already retrieved for the SIRET.
    @param api_client API client with rate limiting.
    @return Tuple (idcc_id, first_idcc) containing the ID and code of the IDCC.
    """
    logger = logging.getLogger("migration")
    idcc_id = None
    first_idcc = None

    # Attempt to retrieve IDCC via SIRET
    if api_data.get("idcc"):
        first_idcc = api_data["idcc"].split(",")[0].strip()
        idcc_id = find_idcc_id(conn_pg, cfg, first_idcc)
        logger.debug(f"IDCC found via SIRET {siret}: {first_idcc}")

    # If no IDCC via SIRET, attempt via SIREN
    if not idcc_id:
        logger.warning(
            f"No IDCC found for SIRET {siret}, searching via SIREN {siren}"
        )

        try:
            api_data_siren = get_api_company_data_siege(siren, api_client)
            if api_data_siren and api_data_siren.get("idcc"):
                first_idcc = api_data_siren["idcc"].split(",")[0].strip()
                idcc_id = find_idcc_id(conn_pg, cfg, first_idcc)
                if idcc_id:
                    logger.info(f"IDCC found via SIREN {siren}: {first_idcc}")
        except Exception as e:
            logger.error(f"Error searching IDCC via SIREN {siren}: {e}")

    # Final log
    if not idcc_id:
        logger.warning(
            f"No IDCC found for company SIREN {siren} (SIRET {siret})"
        )
    else:
        logger.info(f"Final IDCC retained: {first_idcc} (ID: {idcc_id})")

    return idcc_id, first_idcc


def _convert_workforce_range(tranche: str) -> int:
    """! @brief Converts the workforce range to an approximate number.
    @param tranche String representing the workforce range.
    @return Approximate number of employees or None if not convertible.
    """
    if not tranche or not isinstance(tranche, str):
        return None

    import re

    numbers = re.findall(r"\d+", tranche)

    if len(numbers) >= 2:
        min_val = int(numbers[0])
        max_val = int(numbers[1])
        return (min_val + max_val) // 2
    elif len(numbers) == 1:
        return int(numbers[0])

    return None


def _generate_error_report(
    stats: Dict[str, int],
    invalid_sirets: list,
    error_sirets: list,
    laposte_sirets: list,
) -> None:
    """! @brief Generates an error report and saves lists of problematic SIRETs.
    @param stats Statistics dictionary.
    @param invalid_sirets List of invalid SIRETs.
    @param error_sirets List of SIRETs with API errors.
    @param laposte_sirets List of La Poste SIRETs.
    """
    logger = logging.getLogger("migration")

    if not (error_sirets or invalid_sirets):
        logger.info("No SIRETs in error")
        return

    logger.error("=== ERROR SUMMARY ===")

    if stats["laposte_valid"] > 0:
        logger.info(
            f"La Poste SIRETs validated by special rule: {stats['laposte_valid']}"
        )

    if invalid_sirets:
        logger.error(f"Number of invalid SIRETs: {len(invalid_sirets)}")

    if error_sirets:
        logger.error(f"Number of SIRETs with API errors: {len(error_sirets)}")
        logger.error(f"SIRETs with API errors: {', '.join(error_sirets)}")

    # Save to separate files
    if invalid_sirets:
        _save_invalid_sirets_to_file(invalid_sirets)

    if error_sirets:
        _save_error_sirets_to_file(error_sirets)


def _save_invalid_sirets_to_file(invalid_sirets: list) -> None:
    """! @brief Saves the list of invalid SIRETs to a file.
    @param invalid_sirets List of invalid SIRETs.
    """
    logger = logging.getLogger("migration")
    invalid_file = "siret_invalid.txt"

    try:
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write("Invalid SIRETs (validation algorithm failure):\n")
            for siret in invalid_sirets:
                validation_type = (
                    "Format"
                    if len(siret) != 14 or not siret.isdigit()
                    else "La Poste"
                    if siret.startswith("35600")
                    else "Luhn"
                )
                f.write(f"{siret} (error: {validation_type})\n")
        logger.info(f"List of invalid SIRETs saved to {invalid_file}")
    except Exception as e:
        logger.error(f"Error while saving invalid file: {e}")


def _save_error_sirets_to_file(error_sirets: list) -> None:
    """! @brief Saves the list of SIRETs with API errors to a file.
    @param error_sirets List of SIRETs with API errors.
    """
    logger = logging.getLogger("migration")
    error_file = "siret_errors_api.txt"

    try:
        with open(error_file, "w", encoding="utf-8") as f:
            f.write("SIRETs with errors during API call:\n")
            for siret in error_sirets:
                f.write(f"{siret}\n")
        logger.info(f"List of SIRETs with API errors saved to {error_file}")
    except Exception as e:
        logger.error(f"Error while saving API error file: {e}")


# =============================================================================
# OPCO ENRICHMENT VIA DATA.GOUV.FR TABULAR API
# =============================================================================

# Base URL of the data.gouv.fr Tabular API
TABULAR_API_BASE = "https://tabular-api.data.gouv.fr/api"

# Resource ID of the siret_opco file on data.gouv.fr
# Dataset: "Public list of OPCOs and professional branches"
SIRET_OPCO_RESOURCE_ID = "59533036-3c0b-45e6-972c-e967c0a1be17"

# Mapping of normalized OPCO names (to standardize data)
OPCO_NAMES = {
    "AFDAS": "AFDAS",
    "AKTO": "AKTO",
    "ATLAS": "ATLAS",
    "CONSTRUCTYS": "CONSTRUCTYS",
    "L'OPCOMMERCE": "L'OPCOMMERCE",
    "OPCOMMERCE": "L'OPCOMMERCE",
    "OCAPIAT": "OCAPIAT",
    "OPCO 2I": "OPCO 2I",
    "OPCO2I": "OPCO 2I",
    "OPCO EP": "OPCO EP",
    "OPCOEP": "OPCO EP",
    "OPCO MOBILITÉS": "OPCO MOBILITÉS",
    "OPCO MOBILITES": "OPCO MOBILITÉS",
    "OPCO SANTÉ": "OPCO SANTÉ",
    "OPCO SANTE": "OPCO SANTÉ",
    "UNIFORMATION": "UNIFORMATION",
}


def get_opco_by_siret(
    siret: str, api_client: RateLimitedAPI, resource_id: str = SIRET_OPCO_RESOURCE_ID
) -> Optional[str]:
    """! @brief Retrieves the name of the OPCO associated with a SIRET via the Tabular API.
    @param siret Company SIRET number (14 digits).
    @param api_client API client with rate limiting.
    @param resource_id ID of the CSV resource on data.gouv.fr.
    @return Name of the OPCO or None if not found.
    """
    logger = logging.getLogger("migration")

    if not siret or len(siret) != 14 or not siret.isdigit():
        logger.debug(f"Invalid SIRET for OPCO search: {siret}")
        return None

    url = f"{TABULAR_API_BASE}/resources/{resource_id}/data/"
    params = {
        "siret__exact": siret,
        "page_size": 1,
    }

    try:
        response = api_client.request(
            "GET", url, params=params, headers={"Accept": "application/json"}
        )

        if response is None:
            logger.warning(f"No Tabular API response for SIRET {siret}")
            return None

        if response.status_code == 404:
            logger.debug(f"OPCO resource not found: {resource_id}")
            return None

        if response.status_code != 200:
            logger.warning(
                f"Tabular API error for SIRET {siret}: {response.status_code}"
            )
            return None

        data = response.json()
        results = data.get("data", [])

        if not results:
            logger.debug(f"No OPCO found for SIRET {siret}")
            return None

        opco_data = results[0]
        opco_name = (
            opco_data.get("opco")
            or opco_data.get("nom_opco")
            or opco_data.get("OPCO")
            or opco_data.get("NOM_OPCO")
        )

        if opco_name:
            normalized = OPCO_NAMES.get(opco_name.upper().strip(), opco_name.strip())
            logger.debug(f"OPCO found for SIRET {siret}: {normalized}")
            return normalized

        return None

    except Exception as e:
        logger.error(f"Tabular API exception for SIRET {siret}: {e}")
        return None


def get_opco_by_siren(
    siren: str, api_client: RateLimitedAPI, resource_id: str = SIRET_OPCO_RESOURCE_ID
) -> Optional[str]:
    """! @brief Retrieves the name of the OPCO associated with a SIREN via the Tabular API.
    Searches for all SIRETs starting with the SIREN and returns the
    most frequent OPCO (in the case of multiple establishments).
    @param siren Company SIREN number (9 digits).
    @param api_client API client with rate limiting.
    @param resource_id ID of the CSV resource on data.gouv.fr.
    @return Name of the OPCO or None if not found.
    """
    logger = logging.getLogger("migration")

    if not siren or len(siren) != 9 or not siren.isdigit():
        logger.debug(f"Invalid SIREN for OPCO search: {siren}")
        return None

    url = f"{TABULAR_API_BASE}/resources/{resource_id}/data/"
    params = {
        "siret__startswith": siren,
        "page_size": 100,
    }

    try:
        response = api_client.request(
            "GET", url, params=params, headers={"Accept": "application/json"}
        )

        if response is None or response.status_code != 200:
            logger.warning(f"Tabular API error for SIREN {siren}")
            return None

        data = response.json()
        results = data.get("data", [])

        if not results:
            logger.debug(f"No OPCO found for SIREN {siren}")
            return None

        opco_counts: Dict[str, int] = {}
        for row in results:
            opco_name = (
                row.get("opco")
                or row.get("nom_opco")
                or row.get("OPCO")
                or row.get("NOM_OPCO")
            )
            if opco_name:
                normalized = OPCO_NAMES.get(opco_name.upper().strip(), opco_name.strip())
                opco_counts[normalized] = opco_counts.get(normalized, 0) + 1

        if opco_counts:
            most_common = max(opco_counts, key=opco_counts.get)  # type: ignore
            logger.debug(f"OPCO found for SIREN {siren}: {most_common}")
            return most_common

        return None

    except Exception as e:
        logger.error(f"Tabular API exception for SIREN {siren}: {e}")
        return None


def ensure_opco_table(conn: psycopg2.extensions.connection, cfg: Config) -> None:
    """! @brief Creates the opco table if it does not exist in the staging schema.
    @param conn Active PostgreSQL connection.
    @param cfg Configuration containing the schema.
    """
    logger = logging.getLogger("migration")

    with transaction(conn) as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {cfg.pg_schema}.opco (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        logger.info(f"Table {cfg.pg_schema}.opco checked/created")


def get_or_create_opco(
    conn: psycopg2.extensions.connection, cfg: Config, opco_name: str
) -> Optional[int]:
    """! @brief Retrieves the ID of an existing OPCO or creates it if it does not exist.
    @param conn Active PostgreSQL connection.
    @param cfg Configuration containing the schema.
    @param opco_name Name of the OPCO.
    @return ID of the OPCO or None in case of an error.
    """
    logger = logging.getLogger("migration")

    if not opco_name:
        return None

    normalized_name = OPCO_NAMES.get(opco_name.upper().strip(), opco_name.strip())

    try:
        with transaction(conn) as cur:
            cur.execute(
                f"SELECT id FROM {cfg.pg_schema}.opco WHERE name = %s",
                (normalized_name,),
            )
            result = cur.fetchone()

            if result:
                return result[0]

            cur.execute(
                f"""
                INSERT INTO {cfg.pg_schema}.opco (name, updated_at)
                VALUES (%s, CURRENT_TIMESTAMP)
                RETURNING id
                """,
                (normalized_name,),
            )
            new_id = cur.fetchone()[0]
            logger.info(f"OPCO created: {normalized_name} (id={new_id})")
            return new_id

    except Exception as e:
        logger.error(f"Error while creating OPCO {normalized_name}: {e}")
        return None


def add_opco_fk_to_company_info(
    conn: psycopg2.extensions.connection, cfg: Config
) -> bool:
    """! @brief Adds the id_opco (FK) column to the company_info table if it does not exist.
    @param conn Active PostgreSQL connection.
    @param cfg Configuration containing the schema.
    @return True if the column exists or was added, False in case of an error.
    """
    logger = logging.getLogger("migration")

    try:
        with transaction(conn) as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = 'company_info'
                  AND column_name = 'id_opco'
                """,
                (cfg.pg_schema,),
            )

            if cur.fetchone():
                logger.debug("id_opco column already exists in company_info")
                return True

            cur.execute(
                f"""
                ALTER TABLE {cfg.pg_schema}.company_info
                ADD COLUMN id_opco INTEGER REFERENCES {cfg.pg_schema}.opco(id)
                """
            )
            logger.info("id_opco column added to company_info")
            return True

    except Exception as e:
        logger.error(f"Error adding id_opco to company_info: {e}")
        return False


def update_company_opco(
    conn: psycopg2.extensions.connection,
    cfg: Config,
    company_info_id: int,
    opco_id: int,
) -> bool:
    """! @brief Updates a company's OPCO.
    @param conn Active PostgreSQL connection.
    @param cfg Configuration containing the schema.
    @param company_info_id ID of the company in company_info.
    @param opco_id ID of the OPCO.
    @return True if the update was successful, False otherwise.
    """
    try:
        with transaction(conn) as cur:
            cur.execute(
                f"""
                UPDATE {cfg.pg_schema}.company_info
                SET id_opco = %s
                WHERE id = %s
                """,
                (opco_id, company_info_id),
            )
            return True
    except Exception as e:
        logging.getLogger("migration").error(
            f"Error updating OPCO for company_info {company_info_id}: {e}"
        )
        return False


def enrich_companies_with_opco(
    conn: psycopg2.extensions.connection,
    cfg: Config,
    api_client: RateLimitedAPI,
    batch_size: int = 100,
    only_missing: bool = True,
) -> Dict[str, int]:
    """! @brief Enriches companies with their OPCO via the data.gouv.fr Tabular API.
    @param conn Active PostgreSQL connection.
    @param cfg Configuration containing the schema.
    @param api_client API client with rate limiting.
    @param batch_size Number of companies to process per batch.
    @param only_missing If True, only processes companies without an OPCO.
    @return Dictionary with statistics (total, updated, not_found, errors).
    """
    logger = logging.getLogger("migration")
    stats = {"total": 0, "updated": 0, "not_found": 0, "errors": 0}

    # Ensure structures exist
    ensure_opco_table(conn, cfg)
    if not add_opco_fk_to_company_info(conn, cfg):
        logger.error("Could not add id_opco column")
        return stats

    where_clause = "WHERE ci.id_opco IS NULL" if only_missing else ""

    with transaction(conn) as cur:
        cur.execute(
            f"""
            SELECT ci.id, ci.siret
            FROM {cfg.pg_schema}.company_info ci
            {where_clause}
            ORDER BY ci.id
            """
        )
        companies = cur.fetchall()

    stats["total"] = len(companies)
    logger.info(f"OPCO Enrichment: {stats['total']} companies to process")

    for company_id, siret in companies:
        if not siret:
            stats["not_found"] += 1
            continue

        opco_name = get_opco_by_siret(siret, api_client)

        if not opco_name and len(siret) >= 9:
            siren = siret[:9]
            opco_name = get_opco_by_siren(siren, api_client)

        if opco_name:
            opco_id = get_or_create_opco(conn, cfg, opco_name)
            if opco_id and update_company_opco(conn, cfg, company_id, opco_id):
                stats["updated"] += 1
            else:
                stats["errors"] += 1
        else:
            stats["not_found"] += 1

        processed = stats["updated"] + stats["not_found"] + stats["errors"]
        if processed % 100 == 0:
            logger.info(
                f"OPCO progress: {processed}/{stats['total']} "
                f"(updated: {stats['updated']}, not found: {stats['not_found']})"
            )

    logger.info(
        f"OPCO enrichment finished: {stats['updated']} updated, "
        f"{stats['not_found']} not found, {stats['errors']} errors"
    )

    return stats


def get_opco_stats(
    conn: psycopg2.extensions.connection, cfg: Config
) -> List[Tuple[str, int]]:
    """! @brief Retrieves statistics on OPCO distribution.
    @param conn Active PostgreSQL connection.
    @param cfg Configuration containing the schema.
    @return List of tuples (opco_name, number_of_companies).
    """
    with transaction(conn) as cur:
        cur.execute(
            f"""
            SELECT o.name, COUNT(ci.id) as count
            FROM {cfg.pg_schema}.opco o
            LEFT JOIN {cfg.pg_schema}.company_info ci ON ci.id_opco = o.id
            GROUP BY o.name
            ORDER BY count DESC
            """
        )
        return cur.fetchall()


def discover_opco_resource_schema(
    api_client: RateLimitedAPI, resource_id: str = SIRET_OPCO_RESOURCE_ID
) -> Optional[Dict[str, Any]]:
    """! @brief Discovers the schema of an OPCO resource on data.gouv.fr.
    Useful for identifying the available columns in the CSV file.
    @param api_client API client with rate limiting.
    @param resource_id ID of the resource on data.gouv.fr.
    @return Dictionary describing the schema or None in case of an error.
    """
    logger = logging.getLogger("migration")

    url = f"{TABULAR_API_BASE}/resources/{resource_id}/profile/"

    try:
        response = api_client.request(
            "GET", url, headers={"Accept": "application/json"}
        )

        if response is None or response.status_code != 200:
            logger.warning(f"Could not retrieve schema for {resource_id}")
            return None

        return response.json()

    except Exception as e:
        logger.error(f"Error during schema discovery: {e}")
        return None
