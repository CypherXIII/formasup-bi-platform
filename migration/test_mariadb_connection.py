#!/usr/bin/env python3
"""Test script to verify MariaDB connection and data retrieval."""

import pymysql
import logging
from config import Config
from database import ma_execute

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mariadb_connection():
    """Test MariaDB connection and query data for invalid SIRETs."""
    cfg = Config()

    logger.info("Attempting to connect to MariaDB...")
    logger.info(f"Host: {cfg.mariadb_host}, DB: {cfg.mariadb_db}, User: {cfg.mariadb_user}")

    try:
        conn = pymysql.connect(
            host=cfg.mariadb_host,
            user=cfg.mariadb_user,
            password=cfg.mariadb_password,
            database=cfg.mariadb_db,
            port=cfg.mariadb_port,
            connect_timeout=10,
        )
        logger.info("✓ Successfully connected to MariaDB!")

        # Test SIRETs from the migration logs
        test_sirets = [
            '39539439700023',
            '40125156600157',
            '44806188700043',
            '77363330800017',
            '88794358600014',
            '78555589400049'
        ]

        with conn.cursor() as cur:
            for siret in test_sirets:
                logger.info(f"\n=== Testing SIRET: {siret} ===")

                # Try query with discriminator - exact structure that works
                query = """
                    SELECT company.name, city.code, city.name as city_name
                    FROM company
                    LEFT JOIN city ON company.address_city_id = city.id
                    WHERE company.siret = %s
                    AND company.discr LIKE 'company_official%%'
                """

                logger.debug(f"Executing: {query}")
                ma_execute(cur, query, (siret,))
                result = cur.fetchone()

                if result and result[0]:
                    logger.info(f"✓ Found (with discriminator): {result}")
                    logger.info(f"  - Name: {result[0]}")
                    logger.info(f"  - City Code (INSEE): {result[1]}")
                    logger.info(f"  - City Name: {result[2]}")
                else:
                    logger.warning(f"✗ Not found with discriminator, trying without...")

                    # Try without discriminator
                    query2 = """
                        SELECT company.name, city.code, city.name as city_name
                        FROM company
                        LEFT JOIN city ON company.address_city_id = city.id
                        WHERE company.siret = %s
                    """
                    ma_execute(cur, query2, (siret,))
                    result = cur.fetchone()

                    if result and result[0]:
                        logger.info(f"✓ Found (without discriminator): {result}")
                        logger.info(f"  - Name: {result[0]}")
                        logger.info(f"  - City Code (INSEE): {result[1]}")
                        logger.info(f"  - City Name: {result[2]}")
                    else:
                        logger.warning(f"✗ SIRET {siret} not found in MariaDB")

        conn.close()
        logger.info("\n✓ Connection closed successfully")

    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)

if __name__ == "__main__":
    test_mariadb_connection()
