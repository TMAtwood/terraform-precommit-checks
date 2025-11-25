"""
Comprehensive unit tests for check_module_versions.py module.

Tests cover all major code paths and edge cases to ensure >80% code coverage.
"""

import sys
from pathlib import Path
from unittest.mock import patch

from src.check_module_versions import ModuleReference, ModuleVersionChecker, main

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Monkey patch to prevent stdout/stderr wrapping issues in tests

# Save original stdout/stderr
_orig_stdout = sys.stdout
_orig_stderr = sys.stderr

# Restore original stdout/stderr for tests
sys.stdout = _orig_stdout
sys.stderr = _orig_stderr


class TestModuleReference:
    """Test suite for ModuleReference namedtuple."""

    def test_module_reference_creation(self):
        """Test creating a ModuleReference instance."""
        ref = ModuleReference(
            file_path="main.tf",
            line_number=10,
            source="terraform-aws-modules/vpc/aws",
            version="3.0.0",
            git_ref=None,
            normalized_source="terraform-aws-modules/vpc/aws",
        )
        assert ref.file_path == "main.tf"
        assert ref.line_number == 10
        assert ref.source == "terraform-aws-modules/vpc/aws"
        assert ref.version == "3.0.0"
        assert ref.git_ref is None


class TestModuleVersionChecker:
    """Test suite for ModuleVersionChecker class."""

    def test_init(self):
        """Test initialization of ModuleVersionChecker."""
        checker = ModuleVersionChecker()
        assert checker.module_references == {}

    def test_normalize_source_removes_git_refs(self):
        """Test normalize_source removes git refs from source."""
        source = "git::https://github.com/org/repo.git?ref=v1.0.0"
        normalized = ModuleVersionChecker.normalize_source(source)
        assert "ref=" not in normalized
        assert normalized == "https://github.com/org/repo.git"

    def test_normalize_source_removes_git_tags(self):
        """Test normalize_source removes git tags from source."""
        source = "git::https://github.com/org/repo.git?tag=v2.0.0"
        normalized = ModuleVersionChecker.normalize_source(source)
        assert "tag=" not in normalized
        assert normalized == "https://github.com/org/repo.git"

    def test_normalize_source_removes_git_commits(self):
        """Test normalize_source removes git commits from source."""
        source = "git::https://github.com/org/repo.git?commit=abc123"
        normalized = ModuleVersionChecker.normalize_source(source)
        assert "commit=" not in normalized
        assert normalized == "https://github.com/org/repo.git"

    def test_normalize_source_removes_trailing_slashes(self):
        """Test normalize_source removes trailing slashes."""
        source = "terraform-aws-modules/vpc/aws/"
        normalized = ModuleVersionChecker.normalize_source(source)
        assert not normalized.endswith("/")

    def test_normalize_source_removes_git_protocol(self):
        """Test normalize_source removes git:: protocol."""
        source = "git::https://github.com/org/repo.git"
        normalized = ModuleVersionChecker.normalize_source(source)
        assert not normalized.startswith("git::")

    def test_normalize_source_removes_https_protocol(self):
        """Test normalize_source removes https:: protocol."""
        source = "https::github.com/org/repo"
        normalized = ModuleVersionChecker.normalize_source(source)
        assert not normalized.startswith("https::")

    def test_normalize_source_removes_trailing_question_mark(self):
        """Test normalize_source removes trailing ? after removing params."""
        source = "git::https://github.com/org/repo.git?ref=v1.0.0"
        normalized = ModuleVersionChecker.normalize_source(source)
        assert not normalized.endswith("?")

    def test_extract_git_ref_from_ref_parameter(self):
        """Test extract_git_ref extracts ref parameter."""
        source = "git::https://github.com/org/repo.git?ref=v1.0.0"
        git_ref = ModuleVersionChecker.extract_git_ref(source)
        assert git_ref == "v1.0.0"

    def test_extract_git_ref_from_tag_parameter(self):
        """Test extract_git_ref extracts tag parameter."""
        source = "git::https://github.com/org/repo.git?tag=v2.0.0"
        git_ref = ModuleVersionChecker.extract_git_ref(source)
        assert git_ref == "v2.0.0"

    def test_extract_git_ref_from_commit_parameter(self):
        """Test extract_git_ref extracts commit hash."""
        source = "git::https://github.com/org/repo.git?commit=abc123def"
        git_ref = ModuleVersionChecker.extract_git_ref(source)
        assert git_ref == "commit=abc123def"

    def test_extract_git_ref_returns_none_when_not_found(self):
        """Test extract_git_ref returns None when no ref found."""
        source = "terraform-aws-modules/vpc/aws"
        git_ref = ModuleVersionChecker.extract_git_ref(source)
        assert git_ref is None

    def test_parse_module_block_with_registry_module(self):
        """Test parse_module_block parses registry module with version."""
        content = """module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"
}
"""
        checker = ModuleVersionChecker()
        # Start position is after the opening brace of module block
        start_pos = content.index("{") + 1
        module_ref = checker.parse_module_block(content, start_pos, "main.tf", 1)
        assert module_ref is not None
        assert module_ref.source == "terraform-aws-modules/vpc/aws"
        assert module_ref.version == "3.0.0"
        assert module_ref.git_ref is None

    def test_parse_module_block_with_git_source(self):
        """Test parse_module_block parses git source with ref."""
        content = """module "example" {
  source = "git::https://github.com/org/repo.git?ref=v1.0.0"
}
"""
        checker = ModuleVersionChecker()
        start_pos = content.index("{") + 1
        module_ref = checker.parse_module_block(content, start_pos, "main.tf", 1)
        assert module_ref is not None
        assert "github.com/org/repo.git" in module_ref.source
        assert module_ref.git_ref == "v1.0.0"
        assert module_ref.version is None

    def test_parse_module_block_skips_local_path_with_dot_slash(self):
        """Test parse_module_block skips local path starting with ./"""
        content = """
module "local" {
  source = "./modules/my-module"
}
"""
        checker = ModuleVersionChecker()
        module_ref = checker.parse_module_block(content, 16, "main.tf", 2)
        assert module_ref is None

    def test_parse_module_block_skips_local_path_with_double_dot(self):
        """Test parse_module_block skips local path starting with ../"""
        content = """
module "local" {
  source = "../modules/my-module"
}
"""
        checker = ModuleVersionChecker()
        module_ref = checker.parse_module_block(content, 16, "main.tf", 2)
        assert module_ref is None

    def test_parse_module_block_skips_absolute_path(self):
        """Test parse_module_block skips absolute path."""
        content = """
module "local" {
  source = "/absolute/path/to/module"
}
"""
        checker = ModuleVersionChecker()
        module_ref = checker.parse_module_block(content, 16, "main.tf", 2)
        assert module_ref is None

    def test_parse_module_block_handles_malformed_block(self):
        """Test parse_module_block handles malformed blocks gracefully."""
        content = """
module "broken" {
  source = "some-module
"""
        checker = ModuleVersionChecker()
        module_ref = checker.parse_module_block(content, 17, "main.tf", 2)
        # Should return None for malformed block
        assert module_ref is None

    def test_parse_module_block_without_source(self):
        """Test parse_module_block returns None when source is missing."""
        content = """
module "no_source" {
  # No source attribute
}
"""
        checker = ModuleVersionChecker()
        module_ref = checker.parse_module_block(content, 20, "main.tf", 2)
        assert module_ref is None

    def test_check_file_with_module_references(self, tmp_path):
        """Test check_file finds module references in file."""
        test_file = tmp_path / "main.tf"
        test_file.write_text(
            """
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"
}

module "network" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"
}
"""
        )

        checker = ModuleVersionChecker()
        references = checker.check_file(str(test_file))
        assert len(references) == 2

    def test_check_file_handles_read_error(self, capsys):
        """Test check_file handles file read errors gracefully."""
        checker = ModuleVersionChecker()
        references = checker.check_file("nonexistent_file.tf")
        assert references == []
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "Could not read" in captured.out

    def test_check_file_handles_encoding_error(self, capsys):
        """Test check_file handles encoding errors."""
        with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "error")):
            checker = ModuleVersionChecker()
            references = checker.check_file("test.tf")
            assert references == []

    def test_find_conflicts_detects_version_conflicts(self):
        """Test find_conflicts detects conflicting versions."""
        checker = ModuleVersionChecker()
        source = "terraform-aws-modules/vpc/aws"
        checker.module_references[source] = [
            ModuleReference("file1.tf", 1, source, "3.0.0", None, source),
            ModuleReference("file2.tf", 1, source, "4.0.0", None, source),
        ]

        conflicts = checker.find_conflicts()
        assert source in conflicts
        assert len(conflicts[source]) == 2

    def test_find_conflicts_detects_git_ref_conflicts(self):
        """Test find_conflicts detects conflicting git refs."""
        checker = ModuleVersionChecker()
        source = "github.com/org/repo.git"
        checker.module_references[source] = [
            ModuleReference("file1.tf", 1, source, None, "v1.0.0", source),
            ModuleReference("file2.tf", 1, source, None, "v2.0.0", source),
        ]

        conflicts = checker.find_conflicts()
        assert source in conflicts

    def test_find_conflicts_no_conflict_with_same_version(self):
        """Test find_conflicts returns no conflicts when versions match."""
        checker = ModuleVersionChecker()
        source = "terraform-aws-modules/vpc/aws"
        checker.module_references[source] = [
            ModuleReference("file1.tf", 1, source, "3.0.0", None, source),
            ModuleReference("file2.tf", 1, source, "3.0.0", None, source),
        ]

        conflicts = checker.find_conflicts()
        assert source not in conflicts

    def test_find_conflicts_ignores_single_reference(self):
        """Test find_conflicts ignores modules with only one reference."""
        checker = ModuleVersionChecker()
        source = "terraform-aws-modules/vpc/aws"
        checker.module_references[source] = [
            ModuleReference("file1.tf", 1, source, "3.0.0", None, source),
        ]

        conflicts = checker.find_conflicts()
        assert source not in conflicts

    def test_find_conflicts_detects_mixed_version_types(self):
        """Test find_conflicts detects conflicts between version and no-version."""
        checker = ModuleVersionChecker()
        source = "terraform-aws-modules/vpc/aws"
        checker.module_references[source] = [
            ModuleReference("file1.tf", 1, source, "3.0.0", None, source),
            ModuleReference("file2.tf", 1, source, None, None, source),
        ]

        conflicts = checker.find_conflicts()
        assert source in conflicts

    def test_format_conflict_report_with_no_conflicts(self):
        """Test format_conflict_report returns empty string when no conflicts."""
        checker = ModuleVersionChecker()
        report = checker.format_conflict_report({})
        assert report == ""

    def test_format_conflict_report_with_conflicts(self):
        """Test format_conflict_report formats conflicts properly."""
        checker = ModuleVersionChecker()
        source = "terraform-aws-modules/vpc/aws"
        conflicts = {
            source: [
                ModuleReference("file1.tf", 10, source, "3.0.0", None, source),
                ModuleReference("file2.tf", 20, source, "4.0.0", None, source),
            ]
        }

        report = checker.format_conflict_report(conflicts)
        assert "MODULE VERSION CONFLICTS DETECTED" in report
        assert source in report
        assert "file1.tf" in report
        assert "file2.tf" in report
        assert "3.0.0" in report
        assert "4.0.0" in report

    def test_format_conflict_report_with_git_refs(self):
        """Test format_conflict_report formats git ref conflicts."""
        checker = ModuleVersionChecker()
        source = "github.com/org/repo.git"
        conflicts = {
            source: [
                ModuleReference("file1.tf", 10, source, None, "v1.0.0", source),
                ModuleReference("file2.tf", 20, source, None, "v2.0.0", source),
            ]
        }

        report = checker.format_conflict_report(conflicts)
        assert "git ref" in report
        assert "v1.0.0" in report
        assert "v2.0.0" in report

    def test_format_conflict_report_with_no_version(self):
        """Test format_conflict_report handles no version specified."""
        checker = ModuleVersionChecker()
        source = "terraform-aws-modules/vpc/aws"
        conflicts = {
            source: [
                ModuleReference("file1.tf", 10, source, "3.0.0", None, source),
                ModuleReference("file2.tf", 20, source, None, None, source),
            ]
        }

        report = checker.format_conflict_report(conflicts)
        assert "no version specified" in report


class TestMain:
    """Test suite for main() function."""

    def test_main_with_no_files(self, capsys):
        """Test main returns 0 when no files provided."""
        result = main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "No files provided" in captured.out

    def test_main_with_no_conflicts(self, tmp_path, capsys):
        """Test main returns 0 when no conflicts found."""
        test_file = tmp_path / "main.tf"
        test_file.write_text(
            """
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"
}

module "network" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"
}
"""
        )

        result = main([str(test_file)])
        assert result == 0

    def test_main_with_conflicts(self, tmp_path):
        """Test main returns 1 when conflicts found."""
        test_file = tmp_path / "main.tf"
        test_file.write_text(
            """
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"
}

module "network" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "4.0.0"
}
"""
        )

        result = main([str(test_file)])
        assert result == 1

    def test_main_with_verbose_flag(self, tmp_path, capsys):
        """Test main with verbose flag shows additional output."""
        test_file = tmp_path / "main.tf"
        test_file.write_text(
            """
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"
}
"""
        )

        result = main(["-v", str(test_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Scanned" in captured.out or "Found" in captured.out

    def test_main_with_exclude_dir(self, tmp_path):
        """Test main with --exclude-dir filters files."""
        test_dir = tmp_path / "excluded"
        test_dir.mkdir()
        test_file = test_dir / "main.tf"
        test_file.write_text(
            """
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"
}
"""
        )

        result = main(["--exclude-dir", "excluded", str(test_file)])
        assert result == 0

    def test_main_with_multiple_files(self, tmp_path):
        """Test main handles multiple files."""
        file1 = tmp_path / "file1.tf"
        file1.write_text(
            """
module "vpc1" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"
}
"""
        )

        file2 = tmp_path / "file2.tf"
        file2.write_text(
            """
module "vpc2" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"
}
"""
        )

        result = main([str(file1), str(file2)])
        assert result == 0

    def test_main_excludes_multiple_directories(self, tmp_path, capsys):
        """Test main with multiple --exclude-dir options."""
        test_file = tmp_path / "excluded1" / "main.tf"
        test_file.parent.mkdir()
        test_file.write_text('module "test" { source = "test" }')

        result = main(
            ["-v", "--exclude-dir", "excluded1", "--exclude-dir", "excluded2", str(test_file)]
        )
        assert result == 0


class TestRegexPatterns:
    """Test suite for regex patterns."""

    def test_module_block_pattern_matches(self):
        """Test MODULE_BLOCK_PATTERN matches module blocks."""
        content = 'module "vpc" {'
        match = ModuleVersionChecker.MODULE_BLOCK_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "vpc"

    def test_source_pattern_matches(self):
        """Test SOURCE_PATTERN matches source attribute."""
        content = '  source = "terraform-aws-modules/vpc/aws"'
        match = ModuleVersionChecker.SOURCE_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "terraform-aws-modules/vpc/aws"

    def test_version_pattern_matches(self):
        """Test VERSION_PATTERN matches version attribute."""
        content = '  version = "3.0.0"'
        match = ModuleVersionChecker.VERSION_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "3.0.0"

    def test_git_ref_pattern_matches(self):
        """Test GIT_REF_PATTERN matches git ref parameter."""
        source = "git::https://github.com/org/repo.git?ref=v1.0.0"
        match = ModuleVersionChecker.GIT_REF_PATTERN.search(source)
        assert match is not None

    def test_git_commit_pattern_matches(self):
        """Test GIT_COMMIT_PATTERN matches commit parameter."""
        source = (
            "git::https://github.com/org/repo.git?commit=abc123def456"  # pragma: allowlist secret
        )
        match = ModuleVersionChecker.GIT_COMMIT_PATTERN.search(source)
        assert match is not None
        assert match.group(1) == "abc123def456"  # pragma: allowlist secret
