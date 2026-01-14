"""
Test suite for included dcm2niix binaries functionality.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
import pytest

from pypet2bids.dcm2niix4pet import use_included_binary, Dcm2niix4PET
from pypet2bids import helper_functions


class TestIncludedBinaries:
    """Test the included binary functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Remove any existing dcm2niix from environment
        if "DCM2NIIX_PATH" in os.environ:
            del os.environ["DCM2NIIX_PATH"]

    def test_binary_files_exist(self):
        """Test that binary zip files exist."""
        module_folder = Path(__file__).parent.parent / "pypet2bids"
        binary_folder = module_folder / "dcm2niix_binaries"

        assert binary_folder.exists(), "Binary folder does not exist"

        # Check for platform-specific zip files
        zip_files = list(binary_folder.glob("dcm2niix_*.zip"))
        assert len(zip_files) >= 1, "No binary zip files found"

        # Check for expected platforms
        expected_platforms = ["mac", "lnx", "win"]
        found_platforms = [f.stem.split("_")[1] for f in zip_files]
        for platform in expected_platforms:
            assert platform in found_platforms, f"Missing {platform} binary"

    def test_binary_extraction(self):
        """Test that binary extraction works."""
        binary_path = use_included_binary()

        assert binary_path is not None, "Binary extraction failed"
        assert Path(binary_path).exists(), "Extracted binary does not exist"

        # Test that binary is executable
        if os.name != "nt":  # Not Windows
            assert os.access(binary_path, os.X_OK), "Binary is not executable"

    def test_binary_functionality(self):
        """Test that extracted binary actually works."""
        binary_path = use_included_binary()

        if binary_path:
            # Test that binary responds to help command
            result = subprocess.run(
                [binary_path, "-h"], capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0, "Binary help command failed"

    def test_config_file_update(self):
        """Test that config file is updated with binary path."""
        config_path = Path.home() / ".pet2bidsconfig"

        # Backup existing config if it exists
        config_backup = None
        if config_path.exists():
            config_backup = config_path.read_text()
            config_path.unlink()

        try:
            # Extract binary (this should update config)
            binary_path = use_included_binary()

            if binary_path:
                # Check that config was created and updated
                assert config_path.exists(), "Config file was not created"

                saved_path = helper_functions.check_pet2bids_config("DCM2NIIX_PATH")
                assert str(saved_path) == str(
                    binary_path
                ), f"Config path does not match extracted path: {saved_path} != {binary_path}"
        finally:
            # Restore original config if it existed
            if config_backup is not None:
                config_path.write_text(config_backup)
            elif config_path.exists():
                # If we created a new config but there was no original, clean it up
                config_path.unlink()

    def test_dcm2niix4pet_with_included_binary(self):
        """Test that Dcm2niix4PET works with included binary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # This should trigger binary extraction
            converter = Dcm2niix4PET(
                image_folder=temp_path, destination_path=temp_path / "output"
            )

            assert converter.dcm2niix_path is not None, "dcm2niix path not set"
            assert Path(converter.dcm2niix_path).exists(), "dcm2niix binary not found"

    def test_fallback_behavior(self):
        """Test that included binary is used as fallback when system dcm2niix is not available."""
        # Temporarily modify PATH to remove dcm2niix
        original_path = os.environ.get("PATH", "")
        config_path = Path.home() / ".pet2bidsconfig"

        # Backup existing config if it exists
        config_backup = None
        if config_path.exists():
            config_backup = config_path.read_text()
            config_path.unlink()

        try:
            # Remove dcm2niix from PATH
            path_parts = original_path.split(os.pathsep)
            filtered_parts = [p for p in path_parts if "dcm2niix" not in p.lower()]
            os.environ["PATH"] = os.pathsep.join(filtered_parts)

            # Test that included binary is used
            binary_path = use_included_binary()
            assert binary_path is not None, "Fallback to included binary failed"

        finally:
            # Restore original PATH
            os.environ["PATH"] = original_path

            # Restore original config if it existed
            if config_backup is not None:
                config_path.write_text(config_backup)
            elif config_path.exists():
                # If we created a new config but there was no original, clean it up
                config_path.unlink()

    def test_binary_version_compatibility(self):
        """Test that the included binary meets minimum version requirements."""
        binary_path = use_included_binary()

        if binary_path:
            # Test version command
            result = subprocess.run(
                [binary_path, "-v"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                version_output = result.stdout + result.stderr
                # Look for version string like "v1.0.20220720"
                import re

                version_match = re.search(r"v[0-9]+\.[0-9]+\.\d{8}", version_output)
                assert (
                    version_match is not None
                ), f"Could not parse version from: {version_output}"

                version = version_match.group(0)
                minimum_version = "v1.0.20220720"
                assert (
                    version >= minimum_version
                ), f"Version {version} is below minimum {minimum_version}"

    def test_binary_path_consistency(self):
        """Test that the same binary path is returned on multiple calls."""
        config_path = Path.home() / ".pet2bidsconfig"

        # Backup existing config if it exists
        config_backup = None
        if config_path.exists():
            config_backup = config_path.read_text()
            config_path.unlink()

        try:
            # Call multiple times
            path1 = use_included_binary()
            path2 = use_included_binary()

            assert path1 == path2, "Binary path is not consistent across calls"
            assert path1 is not None, "Binary path should not be None"
        finally:
            # Restore original config if it existed
            if config_backup is not None:
                config_path.write_text(config_backup)
            elif config_path.exists():
                # If we created a new config but there was no original, clean it up
                config_path.unlink()

    def test_binary_works_with_dcm2niix4pet_conversion(self):
        """Test that the binary can actually perform a conversion (with dummy data)."""
        binary_path = use_included_binary()

        if binary_path:
            # Test that binary can at least start a conversion process
            # We'll use a non-existent directory to test error handling
            result = subprocess.run(
                [binary_path, "-o", "/tmp", "/nonexistent"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should fail gracefully (not crash)
            assert result.returncode != 0, "Expected failure with nonexistent directory"
            # Should not be a crash (returncode -1 or similar)
            assert result.returncode > -10, "Binary appears to have crashed"
