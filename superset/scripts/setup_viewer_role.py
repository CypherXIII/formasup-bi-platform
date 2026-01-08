#!/usr/bin/env python
"""
Setup Viewer Role Script for FormaSup BI
=========================================

This script configures the 'Viewer' role with dashboard-only permissions.
Run this script after Superset is initialized to set up restricted access.

Usage:
    From Superset container:
    superset shell < setup_viewer_role.py
    
    Or via Flask CLI:
    flask shell < setup_viewer_role.py

Author: Marie Challet
Organization: FormaSup Auvergne
"""

from __future__ import annotations

import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_viewer_permissions() -> List[Tuple[str, str]]:
    """
    Return the list of permissions for dashboard-only access.
    
    Returns:
        List of (permission_name, view_menu_name) tuples
    """
    return [
        # Dashboard access
        ("can_read", "Dashboard"),
        ("can_export", "Dashboard"),
        ("can_get", "DashboardRestApi"),
        ("can_read", "DashboardRestApi"),
        ("can_get_embedded", "DashboardRestApi"),
        ("can_read", "DashboardFilterStateRestApi"),
        ("can_read", "DashboardPermalinkRestApi"),
        ("can_get", "DashboardPermalinkRestApi"),
        
        # Chart access (view only, for dashboard rendering)
        ("can_read", "Chart"),
        ("can_read", "ChartRestApi"),
        ("can_get", "ChartRestApi"),
        ("can_read", "ChartDataRestApi"),
        ("can_get_data", "ChartDataRestApi"),
        
        # Core Superset permissions
        ("can_dashboard", "Superset"),
        ("can_explore_json", "Superset"),
        ("can_slice", "Superset"),
        ("can_csv", "Superset"),
        ("can_language_pack", "Superset"),
        
        # Database/Dataset read access (for filters to work)
        ("can_read", "Database"),
        ("can_read", "Dataset"),
        ("can_read", "DatasetRestApi"),
        
        # API access for dashboard functionality
        ("can_read", "Api"),
        ("can_info", "Api"),
        
        # Menu access
        ("menu_access", "Dashboards"),
        
        # User info (to see own profile)
        ("can_userinfo", "UserDBModelView"),
        ("can_read", "UserRestApi"),
        
        # Common API for translations and config
        ("can_read", "CommonRestApi"),
        ("can_get", "CommonRestApi"),
    ]


def setup_viewer_role() -> None:
    """
    Create and configure the Viewer role with dashboard-only permissions.
    
    This function:
    1. Creates the Viewer role if it does not exist
    2. Clears existing permissions (to ensure clean state)
    3. Adds only the dashboard-viewing permissions
    """
    try:
        from superset import security_manager
        from superset.extensions import db
    except ImportError:
        logger.error("This script must be run within Superset context")
        logger.error("Use: superset shell < setup_viewer_role.py")
        return
    
    logger.info("Setting up Viewer role for dashboard-only access...")
    
    # Find or create Viewer role
    viewer_role = security_manager.find_role("Viewer")
    if not viewer_role:
        viewer_role = security_manager.add_role("Viewer")
        logger.info("Created new 'Viewer' role")
    else:
        logger.info("Found existing 'Viewer' role, updating permissions...")
        # Clear existing permissions for clean setup
        viewer_role.permissions = []
    
    # Add dashboard-only permissions
    permissions_added = 0
    permissions_not_found = []
    
    for perm_name, view_name in get_viewer_permissions():
        perm = security_manager.find_permission_view_menu(perm_name, view_name)
        if perm:
            if perm not in viewer_role.permissions:
                viewer_role.permissions.append(perm)
                permissions_added += 1
        else:
            permissions_not_found.append(f"{perm_name} on {view_name}")
    
    # Commit changes
    db.session.commit()
    
    logger.info(f"Added {permissions_added} permissions to Viewer role")
    
    if permissions_not_found:
        logger.warning(
            f"Some permissions not found (may be version-specific): "
            f"{permissions_not_found[:5]}..."
        )
    
    logger.info("Viewer role setup complete!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Create users with the 'Viewer' role")
    logger.info("2. Configure dashboard access via Dashboard > Edit Properties > Access")
    logger.info("3. Add 'datasource access' permissions for specific tables if needed")


def add_datasource_access(
    role_name: str = "Viewer",
    database_name: str = None,
    schema_name: str = None,
    table_name: str = None,
) -> None:
    """
    Add datasource access permission to a role.
    
    This allows users with the role to view data from specific tables
    in dashboards.
    
    Args:
        role_name: Name of the role to add permission to
        database_name: Name of the database
        schema_name: Schema name (use 'public' for PostgreSQL default)
        table_name: Table name to grant access to
    """
    try:
        from superset import security_manager
        from superset.extensions import db
    except ImportError:
        logger.error("This script must be run within Superset context")
        return
    
    if not all([database_name, table_name]):
        logger.error("database_name and table_name are required")
        return
    
    role = security_manager.find_role(role_name)
    if not role:
        logger.error(f"Role '{role_name}' not found")
        return
    
    # Build the datasource permission name
    # Format: [database].[schema].[table](id:X)
    # We need to find the actual permission
    schema_part = f".{schema_name}" if schema_name else ""
    search_pattern = f"[{database_name}]{schema_part}.[{table_name}]"
    
    # Find matching datasource permissions
    from superset.models.core import Database
    from superset.connectors.sqla.models import SqlaTable
    
    tables = db.session.query(SqlaTable).filter(
        SqlaTable.table_name == table_name
    ).all()
    
    for table in tables:
        perm_name = table.get_perm()
        perm = security_manager.find_permission_view_menu(
            "datasource_access", perm_name
        )
        if perm and perm not in role.permissions:
            role.permissions.append(perm)
            logger.info(f"Added datasource access for '{perm_name}' to {role_name}")
    
    db.session.commit()


def list_viewer_permissions() -> None:
    """List all permissions currently assigned to the Viewer role."""
    try:
        from superset import security_manager
    except ImportError:
        logger.error("This script must be run within Superset context")
        return
    
    viewer_role = security_manager.find_role("Viewer")
    if not viewer_role:
        logger.info("Viewer role does not exist yet")
        return
    
    logger.info(f"Viewer role has {len(viewer_role.permissions)} permissions:")
    for perm in sorted(viewer_role.permissions, key=lambda p: str(p)):
        logger.info(f"  - {perm}")


# Run setup when script is executed
if __name__ == "__main__" or True:
    setup_viewer_role()
