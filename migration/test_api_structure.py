#!/usr/bin/env python3
"""Test script to check API response structure for city info."""

import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_api_structure():
    """Check the structure of the API response."""
    # Test with a known valid SIRET
    test_sirets = [
        "30539439700023",  # ROCKWOOL FRANCE SAS
        "44806188700023",  # MYCLERMONT.FR
    ]

    url = "https://recherche-entreprises.api.gouv.fr/search"

    for siret in test_sirets:
        logger.info(f"\n=== Testing SIRET: {siret} ===")

        params = {
            "q": siret,
            "minimal": "true",
            "include": "matching_etablissements, siege"
        }

        try:
            response = requests.get(url, params=params, headers={"Accept": "application/json"})

            if response.status_code == 200:
                data = response.json()

                if data.get("results"):
                    result = data["results"][0]
                    etablissement = result.get("matching_etablissements", [{}])[0]

                    logger.info(f"\nCompany name fields:")
                    logger.info(f"  nom_raison_sociale: {result.get('nom_raison_sociale')}")
                    logger.info(f"  nom_complet: {result.get('nom_complet')}")

                    logger.info(f"\nEtablissement fields:")
                    for key in sorted(etablissement.keys()):
                        logger.info(f"  {key}: {etablissement[key]}")

                    logger.info(f"\nCity-related fields extracted:")
                    logger.info(f"  commune: {etablissement.get('commune')}")
                    logger.info(f"  code_commune: {etablissement.get('code_commune')}")
                    logger.info(f"  libelle_commune: {etablissement.get('libelle_commune')}")
                    logger.info(f"  commune_code: {etablissement.get('commune_code')}")
                    logger.info(f"  code_postal: {etablissement.get('code_postal')}")
                else:
                    logger.warning(f"No results for {siret}")
            else:
                logger.error(f"API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    check_api_structure()
