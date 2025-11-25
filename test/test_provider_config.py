"""
Comprehensive unit tests for check_provider_config.py module.

Tests cover all major code paths and edge cases to ensure >80% code coverage.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from check_provider_config import ProviderConfigChecker, main


class TestProviderConfigChecker:
    """Test suite for ProviderConfigChecker class."""

    def test_init(self):
        """Test initialization of ProviderConfigChecker."""
        files = ["test1.tf", "test2.tf"]
        checker = ProviderConfigChecker(files)
        assert checker.files == files
        assert checker.errors == []

    def test_is_module_directory_with_variables_tf(self, tmp_path):
        """Test is_module_directory returns True when variables.tf exists."""
        # Create a temporary directory with variables.tf
        variables_file = tmp_path / "variables.tf"
        variables_file.write_text("# variables")
        test_file = tmp_path / "main.tf"
        test_file.write_text("# main")

        checker = ProviderConfigChecker([str(test_file)])
        assert checker.is_module_directory(test_file) is True

    def test_is_module_directory_with_outputs_tf(self, tmp_path):
        """Test is_module_directory returns True when outputs.tf exists."""
        # Create a temporary directory with outputs.tf
        outputs_file = tmp_path / "outputs.tf"
        outputs_file.write_text("# outputs")
        test_file = tmp_path / "main.tf"
        test_file.write_text("# main")

        checker = ProviderConfigChecker([str(test_file)])
        assert checker.is_module_directory(test_file) is True

    def test_is_module_directory_with_modules_path(self, tmp_path):
        """Test is_module_directory returns True when path contains 'modules'."""
        # Create a modules subdirectory
        modules_dir = tmp_path / "modules" / "my-module"
        modules_dir.mkdir(parents=True)
        test_file = modules_dir / "main.tf"
        test_file.write_text("# main")

        checker = ProviderConfigChecker([str(test_file)])
        assert checker.is_module_directory(test_file) is True

    def test_is_module_directory_returns_false(self, tmp_path):
        """Test is_module_directory returns False for non-module directory."""
        test_file = tmp_path / "main.tf"
        test_file.write_text("# main")

        checker = ProviderConfigChecker([str(test_file)])
        assert checker.is_module_directory(test_file) is False

    def test_check_file_non_tf_file(self, tmp_path):
        """Test check_file returns True for non-.tf files."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("not a terraform file")

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True
        assert len(checker.errors) == 0

    def test_check_file_with_old_style_provider(self, tmp_path):
        """Test check_file detects old-style provider configuration."""
        test_file = tmp_path / "test.tf"
        test_file.write_text(
            """
provider "aws" {
  region = "us-east-1"
}
"""
        )

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is False
        assert len(checker.errors) == 1
        assert checker.errors[0][0] == str(test_file)
        assert "aws" in checker.errors[0][2]

    def test_check_file_with_multiple_old_style_providers(self, tmp_path):
        """Test check_file detects multiple old-style provider configurations."""
        test_file = tmp_path / "test.tf"
        test_file.write_text(
            """
provider "aws" {
  region = "us-east-1"
}

provider "azurerm" {
  features {}
}

provider "google" {
  project = "my-project"
}
"""
        )

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is False
        assert len(checker.errors) == 3

    def test_check_file_with_new_style_provider(self, tmp_path):
        """Test check_file passes with new-style provider configuration."""
        test_file = tmp_path / "test.tf"
        test_file.write_text(
            """
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
      configuration_aliases = [aws.main]
    }
  }
}
"""
        )

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True
        assert len(checker.errors) == 0

    def test_check_file_skips_provider_in_required_providers_block(self, tmp_path):
        """Test that providers inside required_providers are not flagged."""
        test_file = tmp_path / "test.tf"
        test_file.write_text(
            """
terraform {
  required_providers {
    provider "aws" {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
"""
        )

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True
        assert len(checker.errors) == 0

    def test_check_file_skips_configuration_aliases(self, tmp_path):
        """Test that configuration_aliases are not flagged."""
        test_file = tmp_path / "test.tf"
        test_file.write_text(
            """
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
      configuration_aliases = [aws.main]
    }
  }
}

provider "aws" {
  alias = "main"
}
"""
        )

        checker = ProviderConfigChecker([str(test_file)])
        # The provider block is within 500 chars of configuration_aliases,
        # so it's skipped by the context check
        result = checker.check_file(str(test_file))
        assert result is True

    def test_check_file_skips_mock_provider(self, tmp_path):
        """Test that mock_provider blocks are not flagged."""
        test_file = tmp_path / "test.tf"
        test_file.write_text(
            """
# This is a mock_provider for testing
provider "aws" {
  region = "us-east-1"
}
"""
        )

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True
        assert len(checker.errors) == 0

    def test_check_file_skips_test_provider(self, tmp_path):
        """Test that test provider blocks are not flagged."""
        test_file = tmp_path / "test.tf"
        test_file.write_text(
            """
# TEST: This is for testing purposes only
provider "aws" {
  region = "us-east-1"
}
"""
        )

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True
        assert len(checker.errors) == 0

    def test_check_file_error_message_for_module(self, tmp_path):
        """Test that module directories get appropriate error message."""
        # Create a module directory with variables.tf
        variables_file = tmp_path / "variables.tf"
        variables_file.write_text("# variables")

        test_file = tmp_path / "main.tf"
        test_file.write_text(
            """
provider "aws" {
  region = "us-east-1"
}
"""
        )

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is False
        assert len(checker.errors) == 1
        error_msg = checker.errors[0][2]
        assert "configuration_aliases" in error_msg
        assert "developer.hashicorp.com" in error_msg

    def test_check_file_error_message_for_root(self, tmp_path):
        """Test that root modules get appropriate error message."""
        test_file = tmp_path / "main.tf"
        test_file.write_text(
            """
provider "aws" {
  region = "us-east-1"
}
"""
        )

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is False
        assert len(checker.errors) == 1
        error_msg = checker.errors[0][2]
        assert "required_providers block" in error_msg

    def test_check_file_handles_read_error(self, tmp_path):
        """Test check_file handles file read errors gracefully."""
        test_file = tmp_path / "nonexistent.tf"

        checker = ProviderConfigChecker([str(test_file)])
        with patch("sys.stderr"):
            result = checker.check_file(str(test_file))
        assert result is False

    def test_check_all_files_returns_true_when_all_pass(self, tmp_path):
        """Test check_all_files returns True when all files pass."""
        file1 = tmp_path / "file1.tf"
        file1.write_text("# no providers")
        file2 = tmp_path / "file2.tf"
        file2.write_text("# also no providers")

        checker = ProviderConfigChecker([str(file1), str(file2)])
        result = checker.check_all_files()
        assert result is True

    def test_check_all_files_returns_false_when_any_fail(self, tmp_path):
        """Test check_all_files returns False when any file fails."""
        file1 = tmp_path / "file1.tf"
        file1.write_text("# no providers")
        file2 = tmp_path / "file2.tf"
        file2.write_text('provider "aws" {\n  region = "us-east-1"\n}')

        checker = ProviderConfigChecker([str(file1), str(file2)])
        result = checker.check_all_files()
        assert result is False

    def test_print_errors_with_no_errors(self, capsys):
        """Test print_errors with no errors does nothing."""
        checker = ProviderConfigChecker([])
        checker.print_errors()
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_print_errors_with_errors(self, capsys, tmp_path):
        """Test print_errors outputs formatted error messages."""
        test_file = tmp_path / "test.tf"
        test_file.write_text('provider "aws" {\n  region = "us-east-1"\n}')

        checker = ProviderConfigChecker([str(test_file)])
        checker.check_file(str(test_file))
        checker.print_errors()

        captured = capsys.readouterr()
        assert "OLD-STYLE PROVIDER CONFIGURATION DETECTED" in captured.err
        assert str(test_file) in captured.err
        assert "RECOMMENDED FIX" in captured.err
        assert "configuration_aliases" in captured.err

    def test_empty_file(self, tmp_path):
        """Test check_file handles empty files."""
        test_file = tmp_path / "empty.tf"
        test_file.write_text("")

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True
        assert len(checker.errors) == 0

    def test_file_with_comments_only(self, tmp_path):
        """Test check_file handles files with only comments."""
        test_file = tmp_path / "comments.tf"
        test_file.write_text("# This is a comment\n// Another comment\n")

        checker = ProviderConfigChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True
        assert len(checker.errors) == 0


class TestMain:
    """Test suite for main() function."""

    def test_main_with_no_files(self, capsys):
        """Test main returns 0 when no files provided."""
        with patch("sys.argv", ["check_provider_config.py"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "No files to check" in captured.err

    def test_main_with_passing_files(self, tmp_path):
        """Test main returns 0 when all files pass."""
        test_file = tmp_path / "test.tf"
        test_file.write_text("# no providers")

        with patch("sys.argv", ["check_provider_config.py", str(test_file)]):
            result = main()
        assert result == 0

    def test_main_with_failing_files(self, tmp_path):
        """Test main returns 1 when files fail."""
        test_file = tmp_path / "test.tf"
        test_file.write_text('provider "aws" {\n  region = "us-east-1"\n}')

        with patch("sys.argv", ["check_provider_config.py", str(test_file)]):
            result = main()
        assert result == 1

    def test_main_with_multiple_files(self, tmp_path):
        """Test main handles multiple files."""
        file1 = tmp_path / "file1.tf"
        file1.write_text("# no providers")
        file2 = tmp_path / "file2.tf"
        file2.write_text("# also no providers")

        with patch("sys.argv", ["check_provider_config.py", str(file1), str(file2)]):
            result = main()
        assert result == 0


class TestRegexPatterns:
    """Test suite for regex patterns."""

    def test_provider_block_pattern_matches_aws(self):
        """Test PROVIDER_BLOCK_PATTERN matches AWS provider."""
        content = 'provider "aws" {'
        match = ProviderConfigChecker.PROVIDER_BLOCK_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "aws"

    def test_provider_block_pattern_matches_azurerm(self):
        """Test PROVIDER_BLOCK_PATTERN matches Azure provider."""
        content = 'provider "azurerm" {'
        match = ProviderConfigChecker.PROVIDER_BLOCK_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "azurerm"

    def test_provider_block_pattern_matches_google(self):
        """Test PROVIDER_BLOCK_PATTERN matches GCP provider."""
        content = 'provider "google" {'
        match = ProviderConfigChecker.PROVIDER_BLOCK_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "google"

    def test_provider_block_pattern_matches_with_whitespace(self):
        """Test PROVIDER_BLOCK_PATTERN matches with various whitespace."""
        content = '  provider  "oci"  {'
        match = ProviderConfigChecker.PROVIDER_BLOCK_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "oci"

    def test_required_providers_pattern_matches(self):
        """Test REQUIRED_PROVIDERS_PATTERN matches required_providers block."""
        content = """
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}
"""
        match = ProviderConfigChecker.REQUIRED_PROVIDERS_PATTERN.search(content)
        assert match is not None
