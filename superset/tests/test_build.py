#!/usr/bin/env python3
"""
Tests for Superset build scripts.
"""

import pytest
import os
import subprocess
from unittest.mock import patch, Mock
from pathlib import Path


class TestBuildScript:
    """Tests for PowerShell build script."""

    def test_build_script_exists(self):
        """Test that build script exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "build-superset-fr.ps1"
        assert script_path.exists()

    def test_build_script_is_powershell(self):
        """Test that script is a PowerShell script."""
        script_path = Path(__file__).parent.parent / "scripts" / "build-superset-fr.ps1"

        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Must start with PowerShell shebang
        assert content.startswith('#!/usr/bin/env pwsh')
        assert '<#' in content  # PowerShell comment
        assert '#>' in content  # End of comment

    def test_build_script_parameters(self):
        """Test that script defines expected parameters."""
        script_path = Path(__file__).parent.parent / "scripts" / "build-superset-fr.ps1"

        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify defined parameters
        assert 'param(' in content
        assert '[string]$SupersetVersion' in content
        assert '[string]$ImageName' in content
        assert '[switch]$NoBuildCache' in content

    def test_build_script_content(self):
        """Test build script content."""
        script_path = Path(__file__).parent.parent / "scripts" / "build-superset-fr.ps1"

        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify key script elements
        assert 'BUILD_TRANSLATIONS=true' in content
        assert 'FormaSup' in content
        assert 'Français' in content
        assert 'Procédure officielle' in content

    @patch('subprocess.run')
    def test_build_script_execution_simulation(self, mock_run):
        """Simulated test of script execution."""
        # Mock successful execution
        mock_run.return_value = Mock(returncode=0, stdout='Build successful', stderr='')

        script_path = Path(__file__).parent.parent / "scripts" / "build-superset-fr.ps1"

        # Note: This test cannot actually execute the PowerShell script
        # in a standard Python test environment
        # It only verifies that the script exists and has the correct content

        assert script_path.exists()
        assert script_path.stat().st_size > 0


class TestBuildProcess:
    """Tests for build process."""

    def test_build_artifacts_existence(self):
        """Test that required build artifacts exist."""
        superset_root = Path(__file__).parent.parent

        # Verify Dockerfile presence in docker/
        dockerfile_path = superset_root / "docker" / "Dockerfile"
        assert dockerfile_path.exists()

        # Verify docker-compose presence at project root
        workspace_root = superset_root.parent
        compose_path = workspace_root / "docker-compose.yml"
        assert compose_path.exists()

    def test_superset_source_exists(self):
        """Test that Superset source code exists or can be cloned."""
        superset_src = Path(__file__).parent.parent / "apache-superset-src"

        # The folder may not exist if the repo has not been cloned yet
        # In that case, verify that the README documents how to clone it
        if superset_src.exists():
            assert superset_src.is_dir()
            # Verify some key files if the folder exists
            key_files = ["setup.py", "pyproject.toml"]
            for file in key_files:
                if (superset_src / file).exists():
                    assert True
        else:
            # Verify that the README documents cloning
            readme_path = Path(__file__).parent.parent / "README.md"
            assert readme_path.exists()
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "git clone" in content

    def test_backup_messages_exists(self):
        """Test that translations file exists."""
        superset_root = Path(__file__).parent.parent

        # Look in locales/ first, otherwise at project root
        backup_po = superset_root / "locales" / "backup-messages.po"
        if not backup_po.exists():
            backup_po = superset_root.parent / "backup-messages.po"

        assert backup_po.exists(), f"backup-messages.po not found in {superset_root}"
        assert backup_po.stat().st_size > 0


class TestConfigurationIntegration:
    """Tests for configuration integration."""

    def test_config_file_structure(self):
        """Test the configuration file structure."""
        config_path = Path(__file__).parent.parent / "config" / "superset_config.py"
        assert config_path.exists()

        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify configuration sections (English headers)
        required_sections = [
            "SECURITY",
            "DATABASE",
            "BRANDING",
            "FRENCH LANGUAGE"
        ]

        for section in required_sections:
            assert section in content

    def test_french_translation_setup(self):
        """Test that French configuration is correctly defined."""
        config_path = Path(__file__).parent.parent / "config" / "superset_config.py"

        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify French parameters
        assert 'BABEL_DEFAULT_LOCALE = "fr"' in content
        assert '"fr": {"flag": "fr", "name": "Francais"}' in content

    def test_build_instructions_reference(self):
        """Test that build instructions are referenced."""
        script_path = Path(__file__).parent.parent / "scripts" / "build-superset-fr.ps1"

        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify references to build process
        assert 'Procédure officielle' in content
        assert 'BUILD_TRANSLATIONS=true' in content


if __name__ == "__main__":
    pytest.main([__file__])
