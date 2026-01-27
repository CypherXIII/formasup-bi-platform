#!/usr/bin/env python3
"""! @file cleanup.py
@brief Data cleaning functions for the migrated tables.
@author Marie Challet
@organization Formasup Auvergne

This module contains functions to clean and normalize data in the temporary
tables before synchronization with the main tables.
"""

import logging
from typing import List, Tuple, Callable

import psycopg2 # type: ignore

from config import Config


def _delete_in_batches(
    conn_pg: psycopg2.extensions.connection,
    logger: logging.Logger,
    delete_sql_template: str,
    batch_size: int,
) -> int:
    """Deletes rows in batches using the provided DELETE ... LIMIT query.

    The delete_sql_template must contain {batch_size} placeholder for the limit.
    Using format string instead of parameter binding because psycopg2 has issues
    with %s inside ctid subqueries. batch_size is always a trusted integer from config.
    """
    total_deleted = 0
    delete_sql = delete_sql_template.format(batch_size=int(batch_size))
    while True:
        with conn_pg.cursor() as cur:
            cur.execute(delete_sql)
            deleted = cur.rowcount
        conn_pg.commit()
        total_deleted += deleted
        if deleted < batch_size:
            break
        logger.debug("Deleted %d rows, continuing next batch", deleted)
    return total_deleted


def cleanup_temp_apprentice_company(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> None:
    """! @brief Cleans up rows with discr like %temp% in the apprentice and company tables.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing the temporary schema name.
    """
    logger = logging.getLogger("migration")
    logger.info("=== Cleaning temporary tables ===")
    schema = cfg.temp_schema

    try:
        with conn_pg.cursor() as cur:
            cur.execute(f"DELETE FROM {schema}.apprentice WHERE discr LIKE '%temp%';")
            cur.execute(f"DELETE FROM {schema}.company WHERE discr LIKE '%temp%';")
        conn_pg.commit()
    except Exception as e:
        conn_pg.rollback()
        logger.exception("Error during temporary table cleanup: %s", e)

        logger.info("Temporary row cleanup finished.")


def sync_corrected_sirets(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> None:
    """! @brief Syncs corrected SIRETs: marks staging companies as 'temp' if MariaDB has them as 'temp'.

    When a SIRET is corrected in MariaDB, the old record gets discr='temp'.
    This function propagates that change to PostgreSQL staging:
    1. Finds SIRETs that are 'temp' in temp schema but 'official' in staging
    2. Updates references (registration, billing) to point to the correct company
    3. Marks the old staging company as 'temp' for later deletion

    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing schema names.
    """
    logger = logging.getLogger("migration")
    logger.info("=== Syncing corrected SIRETs from MariaDB ===")

    try:
        with conn_pg.cursor() as cur:
            # Find SIRETs that are marked as 'temp' in temp schema (from MariaDB)
            # but still exist as 'official' in staging
            cur.execute(f"""
                SELECT tc.siret, sc.id AS staging_id
                FROM {cfg.temp_schema}.company tc
                JOIN {cfg.pg_schema}.company sc ON tc.siret = sc.siret
                WHERE tc.discr LIKE '%temp%'
                  AND sc.discr LIKE '%official%'
                  AND tc.siret IS NOT NULL
                  AND tc.siret != '';
            """)
            corrected_sirets = cur.fetchall()

            if not corrected_sirets:
                logger.info("No corrected SIRETs to sync.")
                return

            logger.info(f"Found {len(corrected_sirets)} SIRETs corrected in MariaDB.")

            for siret, staging_id in corrected_sirets:
                logger.info(f"Processing corrected SIRET {siret} (staging id={staging_id})")

                # Check if there's a replacement company with the same SIREN (first 9 digits)
                siren = siret[:9] if siret and len(siret) >= 9 else None

                if siren:
                    # Look for a valid replacement company with the same SIREN
                    cur.execute(f"""
                        SELECT sc.id
                        FROM {cfg.pg_schema}.company sc
                        WHERE sc.siret LIKE %s
                          AND sc.discr LIKE '%official%'
                          AND sc.id != %s
                        ORDER BY sc.updated_at DESC NULLS LAST
                        LIMIT 1;
                    """, (siren + '%', staging_id))
                    replacement = cur.fetchone()

                    if replacement:
                        replacement_id = replacement[0]
                        logger.info(f"Found replacement company id={replacement_id} for SIRET {siret}")

                        # Update registration references
                        cur.execute(f"""
                            UPDATE {cfg.pg_schema}.registration
                            SET host_company_id = %s
                            WHERE host_company_id = %s;
                        """, (replacement_id, staging_id))
                        reg_updated = cur.rowcount

                        # Update billing references
                        cur.execute(f"""
                            UPDATE {cfg.pg_schema}.billing
                            SET company_id = %s
                            WHERE company_id = %s;
                        """, (replacement_id, staging_id))
                        bill_updated = cur.rowcount

                        logger.info(f"Updated {reg_updated} registrations, {bill_updated} billings")

                # Mark the old company as 'temp' so it gets deleted by cleanup
                cur.execute(f"""
                    UPDATE {cfg.pg_schema}.company
                    SET discr = 'company_temp'
                    WHERE id = %s;
                """, (staging_id,))
                logger.info(f"Marked staging company id={staging_id} as 'temp'")

        conn_pg.commit()
        logger.info("Corrected SIRETs sync complete.")

    except Exception as e:
        conn_pg.rollback()
        logger.exception("Error syncing corrected SIRETs: %s", e)


def cleanup_staging_temp_companies(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> None:
    """! @brief Removes companies marked as 'temp' from the staging schema.

    This cleanup runs on the staging schema (not temp schema) to remove
    companies that were marked as obsolete/corrected.

    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing schema names.
    """
    logger = logging.getLogger("migration")
    logger.info("=== Cleaning obsolete companies from staging ===")
    schema = cfg.pg_schema

    try:
        batch_size = max(100, min(cfg.batch_size, 5000))
        delete_sql = f"""
            DELETE FROM {schema}.company c
            WHERE ctid IN (
                SELECT ctid FROM {schema}.company c
                WHERE c.discr LIKE '%temp%'
                  AND NOT EXISTS (
                      SELECT 1 FROM {schema}.registration r
                      WHERE r.host_company_id = c.id
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM {schema}.billing b
                      WHERE b.company_id = c.id
                  )
                LIMIT {{batch_size}}
            );
        """

        deleted = _delete_in_batches(conn_pg, logger, delete_sql, batch_size)
        logger.info(f"{deleted} obsolete companies deleted from staging.")

    except Exception as e:
        conn_pg.rollback()
        logger.exception("Error cleaning staging temp companies: %s", e)


def cleanup_staging_unreferenced_companies(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> None:
    """! @brief Removes companies in staging with no registrations nor billings.

    This is stricter than temp-only cleanup: any staging company that has no
    registration host reference and no billing reference is deleted, regardless
    of discr. It prevents orphaned companies from lingering when they are no
    longer linked to any business data.
    """
    logger = logging.getLogger("migration")
    schema = cfg.pg_schema
    logger.info("=== Cleaning unreferenced companies from staging ===")

    try:
        batch_size = max(100, min(cfg.batch_size, 5000))
        delete_sql = f"""
            DELETE FROM {schema}.company c
            WHERE ctid IN (
                SELECT ctid FROM {schema}.company c
                WHERE NOT EXISTS (
                    SELECT 1 FROM {schema}.registration r
                    WHERE r.host_company_id = c.id
                )
                AND NOT EXISTS (
                    SELECT 1 FROM {schema}.billing b
                    WHERE b.company_id = c.id
                )
                LIMIT {{batch_size}}
            );
        """

        deleted = _delete_in_batches(conn_pg, logger, delete_sql, batch_size)
        logger.info(f"{deleted} unreferenced companies deleted from staging.")

    except Exception as e:
        conn_pg.rollback()
        logger.exception("Error cleaning unreferenced staging companies: %s", e)


def cleanup_registration(conn_pg: psycopg2.extensions.connection, cfg: Config) -> None:
    """! @brief Cleans the registration table by deleting invalid entries.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing the temporary schema name.
    @note Deletes registrations that:
          - have no associated apprentice
          - have no associated option
          - are marked as deleted (deleted_at is not NULL)
          - have a status that contains 'double'
    """
    logger = logging.getLogger("migration")
    schema = cfg.temp_schema
    logger.info("=== Cleaning registration table ===")
    try:
        with conn_pg.cursor() as cur:
            cur.execute(
                f"DELETE FROM {schema}.registration WHERE apprentice_id IS NULL OR option_id IS NULL OR deleted_at IS NOT NULL OR status LIKE '%double%' OR start_date < '2022-06-01' OR draft=1 ;"
            )
            cnt = cur.rowcount
        conn_pg.commit()
        logger.info("%d records deleted.", cnt)
    except Exception as e:
        conn_pg.rollback()
        logger.exception("Error cleaning up registration: %s", e)


def cleanup_apprentice_city(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> None:
    """! @brief Cleans up cities in the apprentice table by replacing temporary city IDs
    with valid city IDs based on their code.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing the temporary schema name.
    """
    logger = logging.getLogger("migration")
    logger.info("=== Cleaning cities in apprentice ===")

    try:
        with conn_pg.cursor() as cur:
            # Create a mapping table between temporary and valid city IDs
            cur.execute(f"""
            DROP TABLE IF EXISTS temp_city_mapping;

            SELECT
                ct.id AS temp_city_id,
                c.id AS valid_city_id
            INTO TEMP TABLE temp_city_mapping
            FROM {cfg.temp_schema}.city ct
            JOIN {cfg.pg_schema}.city c ON ct.code = c.code
            WHERE ct.id != c.id;
            """)

            # Count the number of mappings for logging
            cur.execute("SELECT COUNT(*) FROM temp_city_mapping")
            mapping_count = cur.fetchone()[0]

            # Update city IDs in apprentice
            cur.execute(f"""
            UPDATE {cfg.temp_schema}.apprentice a
            SET address_city_id = m.valid_city_id
            FROM temp_city_mapping m
            WHERE a.address_city_id = m.temp_city_id;
            """)
            updated_count = cur.rowcount

            # Delete the temporary table
            cur.execute("DROP TABLE IF EXISTS temp_city_mapping;")

        conn_pg.commit()
        logger.info(
            f"Cities cleaned: {mapping_count} mappings found, {updated_count} apprentices updated."
        )

    except Exception as e:
        conn_pg.rollback()
        logger.exception(f"Error during city cleanup: {e}")


def cleanup_unreferenced_training(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> None:
    """! @brief Removes training records not linked to valid registrations.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing the temporary schema name.
    @note Training records are kept only if they have at least one registration
          with a signature_date after 2022-06-30.
    """
    logger = logging.getLogger("migration")
    schema = cfg.temp_schema
    logger.info("=== Cleaning unreferenced training records ===")

    try:
        batch_size = max(100, min(cfg.batch_size, 5000))
        delete_sql = f"""
            DELETE FROM {schema}.training t
            WHERE ctid IN (
                SELECT ctid FROM {schema}.training t
                WHERE NOT EXISTS (
                    SELECT 1 FROM {schema}.training_course tc
                    JOIN {schema}.training_group tg ON tg.course_id = tc.id
                    JOIN {schema}.training_option topt ON topt.group_id = tg.id
                    JOIN {schema}.registration r ON r.option_id = topt.id
                    WHERE tc.training_id = t.id
                      AND r.signature_date IS NOT NULL
                      AND r.signature_date > DATE '2022-06-30'
                )
                LIMIT {{batch_size}}
            );
        """

        deleted_count = _delete_in_batches(conn_pg, logger, delete_sql, batch_size)
        logger.info(f"{deleted_count} unreferenced training records deleted.")

    except Exception as e:
        conn_pg.rollback()
        logger.exception("Error during unreferenced training cleanup: %s", e)


def cleanup_unreferenced_rncp(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> None:
    """! @brief Removes RNCP records that are not referenced by any training.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing the temporary schema name.
    @note RNCP records are kept only if:
          - Their id is referenced in training.rncp_id
          - OR their code matches training.rncp_number
    """
    logger = logging.getLogger("migration")
    schema = cfg.temp_schema
    logger.info("=== Cleaning unreferenced RNCP records ===")

    try:
        batch_size = max(100, min(cfg.batch_size, 5000))
        delete_sql = f"""
            DELETE FROM {schema}.rncp r
            WHERE ctid IN (
                SELECT ctid FROM {schema}.rncp r
                WHERE r.id NOT IN (
                    SELECT rncp_id FROM {schema}.training WHERE rncp_id IS NOT NULL
                )
                AND r.code NOT IN (
                    SELECT rncp_number FROM {schema}.training WHERE rncp_number IS NOT NULL
                )
                LIMIT {{batch_size}}
            );
        """

        deleted_count = _delete_in_batches(conn_pg, logger, delete_sql, batch_size)
        logger.info(f"{deleted_count} unreferenced RNCP records deleted.")

    except Exception as e:
        conn_pg.rollback()
        logger.exception("Error during unreferenced RNCP cleanup: %s", e)


def cleanup_obsolete_companies(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> None:
    """! @brief Removes obsolete companies (those with no registrations or billings).
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing the temporary schema name.
    @note Obsolete companies are those that:
          - Have no associated registrations
          - Have no associated billings
    """
    logger = logging.getLogger("migration")
    schema = cfg.temp_schema
    logger.info("=== Cleaning obsolete companies ===")

    try:
        batch_size = max(100, min(cfg.batch_size, 5000))
        delete_sql = f"""
            DELETE FROM {schema}.company c
            WHERE ctid IN (
                SELECT ctid FROM {schema}.company c
                WHERE NOT EXISTS (
                    SELECT 1 FROM {schema}.registration r
                    WHERE r.host_company_id = c.id
                )
                AND NOT EXISTS (
                    SELECT 1 FROM {schema}.billing b
                    WHERE b.company_id = c.id
                )
                LIMIT {{batch_size}}
            );
        """

        deleted_count = _delete_in_batches(conn_pg, logger, delete_sql, batch_size)
        logger.info(f"{deleted_count} obsolete companies deleted.")

    except Exception as e:
        conn_pg.rollback()
        logger.exception("Error during obsolete companies cleanup: %s", e)


def run_specific_cleanup(conn_pg: psycopg2.extensions.connection, cfg: Config) -> None:
    """! @brief Executes a series of specific cleanups on the migrated data.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing the temporary schema name.
    @note Performs several cleaning operations:
          1. Uppercasing
          2. Deletion of deadlines and invoices marked as deleted
          3. Normalization of names (uppercase) and first names (first letter capitalized)
          4. Cleaning of dimension tables to keep only entries
          referenced in the main tables.
    """
    logger = logging.getLogger("migration")
    schema = cfg.temp_schema
    logger.info("=== Specific cleanups ===")
    try:
        # Merge companies with duplicate SIRET
        logger.info("Merging companies with duplicate SIRET...")

        with conn_pg.cursor() as cur:
            # Create a temporary table for duplicate mappings
            cur.execute(f"""
            DROP TABLE IF EXISTS {schema}.company_duplicate_map;

            WITH duplicates AS (
                SELECT id, siret, updated_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY siret
                        ORDER BY updated_at DESC, id DESC
                    ) AS rank
                FROM {schema}.company
                WHERE siret IS NOT NULL AND siret != ''
            )
            SELECT d1.id AS id_to_delete, d2.id AS id_to_keep
            INTO {schema}.company_duplicate_map
            FROM duplicates d1
            JOIN duplicates d2 ON d1.siret = d2.siret AND d2.rank = 1
            WHERE d1.rank > 1;
            """)

            # Get the number of duplicates for logging
            cur.execute(f"SELECT COUNT(*) FROM {schema}.company_duplicate_map;")
            duplicate_count = cur.fetchone()[0]  # type: ignore

        conn_pg.commit()
        logger.info(f"Found {duplicate_count} companies with duplicate SIRET.")

        if duplicate_count > 0:
            # Update references in other tables
            with conn_pg.cursor() as cur:
                # Update references in registration
                cur.execute(f"""
                UPDATE {schema}.registration r
                SET host_company_id = m.id_to_keep
                FROM {schema}.company_duplicate_map m
                WHERE r.host_company_id = m.id_to_delete;
                """)
                reg_updates = cur.rowcount

                # Update references in billing
                cur.execute(f"""
                UPDATE {schema}.billing b
                SET company_id = m.id_to_keep
                FROM {schema}.company_duplicate_map m
                WHERE b.company_id = m.id_to_delete;
                """)
                bill_updates = cur.rowcount

                # Delete duplicate companies
                cur.execute(f"""
                DELETE FROM {schema}.company c
                USING {schema}.company_duplicate_map m
                WHERE c.id = m.id_to_delete;
                """)
                deleted = cur.rowcount

            conn_pg.commit()
            logger.info(f"{reg_updates} registrations updated.")
            logger.info(f"{bill_updates} billings updated.")
            logger.info(f"{deleted} duplicate companies deleted.")

            # Clean up the mapping table
            with conn_pg.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {schema}.company_duplicate_map;")
            conn_pg.commit()

        logger.info("Deleting deadlines with deleted_at not NULL...")

        with conn_pg.cursor() as cur:
            cur.execute(f"DELETE FROM {schema}.deadline WHERE deleted_at IS NOT NULL;")
            d_cnt = cur.rowcount
        conn_pg.commit()
        logger.info("%d deadlines deleted.", d_cnt)

        with conn_pg.cursor() as cur:
            cur.execute(f"DELETE FROM {schema}.billing WHERE deleted_at IS NOT NULL;")
            b_cnt = cur.rowcount
        conn_pg.commit()
        logger.info("%d invoices deleted.", b_cnt)

        with conn_pg.cursor() as cur:
            cur.execute(
                f"DELETE FROM {schema}.billing_line WHERE deleted_at IS NOT NULL;"
            )
            bl_cnt = cur.rowcount
        conn_pg.commit()
        logger.info("%d invoice lines deleted.", bl_cnt)

        logger.info("Names/first names formatted.")
        with conn_pg.cursor() as cur:
            cur.execute(f"UPDATE {schema}.apprentice SET last_name = UPPER(last_name);")
            cur.execute(
                f"UPDATE {schema}.apprentice SET first_name = INITCAP(first_name);"
            )
        conn_pg.commit()

        logger.info("Cleaning dimension tables...")
        dimension_cleanup = {
            "company": {
                "key": "id",
                "references": [
                    ("registration", "host_company_id"),
                    ("billing", "company_id"),
                ],
            },
            "apprentice": {
                "key": "id",
                "references": [("registration", "apprentice_id")],
            },
            "sector": {"key": "id", "references": [("training", "sector_id")]},
            "training_option": {
                "key": "id",
                "references": [("registration", "option_id")],
            },
            "training_group": {
                "key": "id",
                "references": [("training_option", "group_id")],
            },
            "training_course": {
                "key": "id",
                "references": [("training_group", "course_id")],
            },
            "training": {
                "key": "id",
                "references": [("training_course", "training_id")],
            },
        }
        for table, conf in dimension_cleanup.items():
            key = conf["key"]
            subs: List[str] = []
            for ref in conf["references"]:
                tbl, col = ref[0], ref[1]
                expr = f"{schema}.{tbl}.{col}"
                if len(ref) == 3:
                    expr = ref[2].format(col=expr)
                subs.append(
                    f"SELECT {expr} FROM {schema}.{tbl} WHERE {col} IS NOT NULL"
                )
            union = " UNION ".join(subs)
            sql = f"DELETE FROM {schema}.{table} WHERE {key} NOT IN ({union});"
            with conn_pg.cursor() as cur:
                cur.execute(sql)
                cnt = cur.rowcount
            conn_pg.commit()
            logger.info("%d rows deleted from %s.", cnt, table)

    except Exception as e:
        conn_pg.rollback()
        logger.exception("Specific cleanup error: %s", e)


# List of cleanup tasks
CLEANUP_TASKS: List[Tuple[str, Callable]] = [  # type: ignore
    ("cleanup_temp_apprentice_company", cleanup_temp_apprentice_company),
    ("sync_corrected_sirets", sync_corrected_sirets),
    ("cleanup_registration", cleanup_registration),
    ("cleanup_apprentice_city", cleanup_apprentice_city),
    ("cleanup_unreferenced_training", cleanup_unreferenced_training),
    ("cleanup_unreferenced_rncp", cleanup_unreferenced_rncp),
    ("cleanup_obsolete_companies", cleanup_obsolete_companies),
    ("specific_cleanup", run_specific_cleanup),
    ("cleanup_staging_temp_companies", cleanup_staging_temp_companies),
    ("cleanup_staging_unreferenced_companies", cleanup_staging_unreferenced_companies),
]


def run_cleanup(conn_pg: psycopg2.extensions.connection, cfg: Config) -> None:
    """! @brief Sequentially executes all registered cleanup tasks.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing schemas and other settings.
    """
    logger = logging.getLogger("migration")
    for name, fn in CLEANUP_TASKS:
        logger.info("Executing cleanup: %s", name)
        try:
            fn(conn_pg, cfg)
        except Exception as e:
            logger.exception("Error in %s: %s", name, e)
