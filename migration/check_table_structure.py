#!/usr/bin/env python3
"""Test script to check MariaDB company table structure."""

import pymysql
import logging
from config import Config
from database import ma_execute

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_company_table_structure():
    """Check the structure of the company table."""
    cfg = Config()

    try:
        conn = pymysql.connect(
            host=cfg.mariadb_host,
            user=cfg.mariadb_user,
            password=cfg.mariadb_password,
            database=cfg.mariadb_db,
            port=cfg.mariadb_port,
            connect_timeout=10,
        )
        logger.info("✓ Connected to MariaDB")

        with conn.cursor() as cur:
            # Get company table structure
            logger.info("\n=== Company Table Structure ===")
            ma_execute(cur, "DESCRIBE company")
            rows = cur.fetchall()
            for row in rows:
                logger.info(f"{row[0]}: {row[1]} (NULL: {row[2]}, Key: {row[3]}, Default: {row[4]})")

            # Get city table structure
            logger.info("\n=== City Table Structure ===")
            ma_execute(cur, "DESCRIBE city")
            rows = cur.fetchall()
            for row in rows:
                logger.info(f"{row[0]}: {row[1]} (NULL: {row[2]}, Key: {row[3]}, Default: {row[4]})")

            # Test query with correct columns
            logger.info("\n=== Testing Correct Query ===")
            query = """
                SELECT DISTINCT co.name, c.name as city_name, c.code as city_code
                FROM company co
                LEFT JOIN city c ON co.address_city_id = c.id
                WHERE co.siret = %s
                AND co.discr LIKE 'company_official%%'
                LIMIT 1
            """
            test_siret = '39539439700023'
            logger.info(f"Query for SIRET {test_siret}:")
            ma_execute(cur, query, (test_siret,))
            result = cur.fetchone()
            if result:
                logger.info(f"✓ Result: {result}")
            else:
                logger.warning(f"✗ No result for {test_siret}")

        conn.close()

    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)

if __name__ == "__main__":
    check_company_table_structure()
