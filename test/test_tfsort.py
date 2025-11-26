"""
Comprehensive unit tests for check_tfsort.py module.

Tests cover all major code paths and edge cases to ensure >80% code coverage.
"""

import sys
from pathlib import Path
from unittest.mock import patch

from src.check_tfsort import BlockInfo, TFSortChecker, main

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Monkey patch to prevent stdout/stderr wrapping issues in tests

# Save original stdout/stderr
_orig_stdout = sys.stdout
_orig_stderr = sys.stderr

# Restore original stdout/stderr for tests
sys.stdout = _orig_stdout
sys.stderr = _orig_stderr


class TestBlockInfo:
    """Test suite for BlockInfo namedtuple."""

    def test_block_info_creation(self):
        """Test creating a BlockInfo instance."""
        block = BlockInfo(
            block_type="variable",
            name="region",
            line_number=10,
            content='variable "region" {\n  type = string\n}',
        )
        assert block.block_type == "variable"
        assert block.name == "region"
        assert block.line_number == 10
        assert "variable" in block.content


class TestTFSortChecker:
    """Test suite for TFSortChecker class."""

    def test_init(self):
        """Test initialization of TFSortChecker."""
        files = ["test1.tf", "test2.tf"]
        checker = TFSortChecker(files)
        assert checker.files == files
        assert checker.errors == []

    def test_find_block_end_simple_block(self):
        """Test find_block_end with simple block."""
        content = 'variable "test" {\n  type = string\n}'
        start_pos = content.index("{")
        end_pos = TFSortChecker.find_block_end(content, start_pos)
        assert content[end_pos] == "}"

    def test_find_block_end_nested_block(self):
        """Test find_block_end with nested blocks."""
        content = 'variable "test" {\n  validation {\n    condition = true\n  }\n}'
        start_pos = content.index("{")
        end_pos = TFSortChecker.find_block_end(content, start_pos)
        assert content[end_pos] == "}"
        assert end_pos == len(content) - 1

    def test_find_block_end_no_closing_brace(self):
        """Test find_block_end when no closing brace exists."""
        content = 'variable "test" {'
        start_pos = content.index("{")
        end_pos = TFSortChecker.find_block_end(content, start_pos)
        assert end_pos == len(content)

    def test_extract_blocks_variable(self):
        """Test extract_blocks finds variable blocks."""
        content = """
variable "region" {
  type = string
}

variable "instance_type" {
  type = string
}
"""
        checker = TFSortChecker([])
        blocks = checker.extract_blocks(content, "variable")
        assert len(blocks) == 2
        assert blocks[0].name == "region"
        assert blocks[1].name == "instance_type"

    def test_extract_blocks_output(self):
        """Test extract_blocks finds output blocks."""
        content = """
output "vpc_id" {
  value = aws_vpc.main.id
}

output "subnet_ids" {
  value = aws_subnet.main[*].id
}
"""
        checker = TFSortChecker([])
        blocks = checker.extract_blocks(content, "output")
        assert len(blocks) == 2
        assert blocks[0].name == "vpc_id"
        assert blocks[1].name == "subnet_ids"

    def test_extract_blocks_locals(self):
        """Test extract_blocks finds locals blocks."""
        content = """
locals {
  common_tags = {
    Environment = "production"
  }
}
"""
        checker = TFSortChecker([])
        blocks = checker.extract_blocks(content, "locals")
        assert len(blocks) == 1
        assert blocks[0].name == ""
        assert blocks[0].block_type == "locals"

    def test_extract_blocks_terraform(self):
        """Test extract_blocks finds terraform blocks."""
        content = """
terraform {
  required_version = ">= 1.0"
}
"""
        checker = TFSortChecker([])
        blocks = checker.extract_blocks(content, "terraform")
        assert len(blocks) == 1
        assert blocks[0].name == ""
        assert blocks[0].block_type == "terraform"

    def test_extract_blocks_invalid_type(self):
        """Test extract_blocks returns empty list for invalid type."""
        content = 'variable "test" {}'
        checker = TFSortChecker([])
        blocks = checker.extract_blocks(content, "invalid")
        assert blocks == []

    def test_extract_blocks_with_line_numbers(self):
        """Test extract_blocks calculates correct line numbers."""
        content = """\nvariable "b" {
  type = string
}

variable "a" {
  type = string
}
"""
        checker = TFSortChecker([])
        blocks = checker.extract_blocks(content, "variable")
        # Count the newlines to verify line numbers are calculated correctly
        # First block contains initial newline, so starts at line 1
        assert blocks[0].line_number == 1
        # Second block starts at line 5 (after blank line)
        assert blocks[1].line_number == 5

    def test_check_block_order_sorted(self):
        """Test check_block_order passes for sorted blocks."""
        blocks = [
            BlockInfo("variable", "aaa", 1, ""),
            BlockInfo("variable", "bbb", 5, ""),
            BlockInfo("variable", "ccc", 10, ""),
        ]
        checker = TFSortChecker([])
        errors = checker.check_block_order(blocks, "test.tf")
        assert len(errors) == 0

    def test_check_block_order_unsorted(self):
        """Test check_block_order detects unsorted blocks."""
        blocks = [
            BlockInfo("variable", "bbb", 5, ""),
            BlockInfo("variable", "aaa", 1, ""),
            BlockInfo("variable", "ccc", 10, ""),
        ]
        checker = TFSortChecker([])
        errors = checker.check_block_order(blocks, "test.tf")
        assert len(errors) == 1
        assert "aaa" in errors[0][2]
        assert "bbb" in errors[0][2]

    def test_check_block_order_case_insensitive(self):
        """Test check_block_order sorts case-insensitively."""
        blocks = [
            BlockInfo("variable", "BBB", 1, ""),
            BlockInfo("variable", "AAA", 5, ""),
            BlockInfo("variable", "ccc", 10, ""),
        ]
        checker = TFSortChecker([])
        errors = checker.check_block_order(blocks, "test.tf")
        # Should detect disorder - case insensitive, AAA should come before BBB
        assert len(errors) == 1

    def test_check_block_order_single_block(self):
        """Test check_block_order passes for single block."""
        blocks = [BlockInfo("variable", "test", 1, "")]
        checker = TFSortChecker([])
        errors = checker.check_block_order(blocks, "test.tf")
        assert len(errors) == 0

    def test_check_block_order_empty_list(self):
        """Test check_block_order passes for empty list."""
        checker = TFSortChecker([])
        errors = checker.check_block_order([], "test.tf")
        assert len(errors) == 0

    def test_check_file_non_tf_file(self, tmp_path):
        """Test check_file returns True for non-.tf files."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("not a terraform file")

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True

    def test_check_file_sorted_variables(self, tmp_path):
        """Test check_file passes for sorted variables.tf."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text(
            """
variable "aaa" {
  type = string
}

variable "bbb" {
  type = string
}

variable "ccc" {
  type = string
}
"""
        )

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True
        assert len(checker.errors) == 0

    def test_check_file_unsorted_variables(self, tmp_path):
        """Test check_file detects unsorted variables.tf."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text(
            """
variable "ccc" {
  type = string
}

variable "aaa" {
  type = string
}

variable "bbb" {
  type = string
}
"""
        )

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is False
        assert len(checker.errors) > 0

    def test_check_file_sorted_outputs(self, tmp_path):
        """Test check_file passes for sorted outputs.tf."""
        test_file = tmp_path / "outputs.tf"
        test_file.write_text(
            """
output "aaa" {
  value = "aaa"
}

output "bbb" {
  value = "bbb"
}
"""
        )

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True

    def test_check_file_unsorted_outputs(self, tmp_path):
        """Test check_file detects unsorted outputs.tf."""
        test_file = tmp_path / "outputs.tf"
        test_file.write_text(
            """
output "zzz" {
  value = "zzz"
}

output "aaa" {
  value = "aaa"
}
"""
        )

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is False
        assert len(checker.errors) > 0

    def test_check_file_with_variable_keyword_in_content(self, tmp_path):
        """Test check_file checks files containing 'variable' keyword."""
        test_file = tmp_path / "main.tf"
        test_file.write_text(
            """
variable "zzz" {
  type = string
}

variable "aaa" {
  type = string
}
"""
        )

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is False

    def test_check_file_with_output_keyword_in_content(self, tmp_path):
        """Test check_file checks files containing 'output' keyword."""
        test_file = tmp_path / "main.tf"
        test_file.write_text(
            """
output "zzz" {
  value = "zzz"
}

output "aaa" {
  value = "aaa"
}
"""
        )

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is False

    def test_check_file_handles_read_error(self, tmp_path, capsys):
        """Test check_file handles file read errors gracefully."""
        test_file = tmp_path / "nonexistent.tf"

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is False
        captured = capsys.readouterr()
        assert "Error reading" in captured.err

    def test_check_file_empty_file(self, tmp_path):
        """Test check_file handles empty files."""
        test_file = tmp_path / "empty.tf"
        test_file.write_text("")

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True

    def test_check_file_no_blocks(self, tmp_path):
        """Test check_file handles files with no variable/output blocks."""
        test_file = tmp_path / "resources.tf"
        test_file.write_text(
            """
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
"""
        )

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True

    def test_run_all_files_pass(self, tmp_path, capsys):
        """Test run returns 0 when all files pass."""
        file1 = tmp_path / "variables.tf"
        file1.write_text('variable "aaa" {}\nvariable "bbb" {}')

        checker = TFSortChecker([str(file1)])
        result = checker.run()
        assert result == 0
        captured = capsys.readouterr()
        assert "properly sorted" in captured.out

    def test_run_some_files_fail(self, tmp_path, capsys):
        """Test run returns 1 when some files fail."""
        file1 = tmp_path / "variables.tf"
        file1.write_text('variable "zzz" {}\nvariable "aaa" {}')

        checker = TFSortChecker([str(file1)])
        result = checker.run()
        assert result == 1
        captured = capsys.readouterr()
        assert "TFSort Compliance Check Failed" in captured.out

    def test_run_with_no_files(self, capsys):
        """Test run with empty file list."""
        checker = TFSortChecker([])
        result = checker.run()
        assert result == 0

    def test_run_prints_errors(self, tmp_path, capsys):
        """Test run prints formatted errors."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text('variable "zzz" {}\nvariable "aaa" {}')

        checker = TFSortChecker([str(test_file)])
        result = checker.run()
        assert result == 1
        captured = capsys.readouterr()
        assert "File:" in captured.out
        assert "Line:" in captured.out
        assert "tfsort" in captured.out


class TestMain:
    """Test suite for main() function."""

    def test_main_with_no_files(self, capsys):
        """Test main returns 0 when no files provided."""
        with patch("sys.argv", ["check_tfsort.py"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "No files to check" in captured.err

    def test_main_with_passing_files(self, tmp_path):
        """Test main returns 0 when all files pass."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text('variable "aaa" {}\nvariable "bbb" {}')

        with patch("sys.argv", ["check_tfsort.py", str(test_file)]):
            result = main()
        assert result == 0

    def test_main_with_failing_files(self, tmp_path):
        """Test main returns 1 when files fail."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text('variable "zzz" {}\nvariable "aaa" {}')

        with patch("sys.argv", ["check_tfsort.py", str(test_file)]):
            result = main()
        assert result == 1

    def test_main_with_all_files_flag(self, tmp_path):
        """Test main with --all-files flag."""
        test_file = tmp_path / "test.tf"
        test_file.write_text('variable "aaa" {}')

        with patch("sys.argv", ["check_tfsort.py", "--all-files"]), patch(
            "pathlib.Path.rglob", return_value=[test_file]
        ):
            result = main()
        assert result == 0

    def test_main_with_multiple_files(self, tmp_path):
        """Test main handles multiple files."""
        file1 = tmp_path / "variables.tf"
        file1.write_text('variable "aaa" {}')
        file2 = tmp_path / "outputs.tf"
        file2.write_text('output "bbb" { value = "bbb" }')

        with patch("sys.argv", ["check_tfsort.py", str(file1), str(file2)]):
            result = main()
        assert result == 0


class TestRegexPatterns:
    """Test suite for regex patterns."""

    def test_variable_pattern_matches(self):
        """Test VARIABLE_PATTERN matches variable blocks."""
        content = 'variable "test" {'
        match = TFSortChecker.VARIABLE_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "test"

    def test_variable_pattern_with_whitespace(self):
        """Test VARIABLE_PATTERN matches with various whitespace."""
        content = '  variable  "test"  {'
        match = TFSortChecker.VARIABLE_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "test"

    def test_output_pattern_matches(self):
        """Test OUTPUT_PATTERN matches output blocks."""
        content = 'output "test" {'
        match = TFSortChecker.OUTPUT_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "test"

    def test_output_pattern_with_whitespace(self):
        """Test OUTPUT_PATTERN matches with various whitespace."""
        content = '  output  "test"  {'
        match = TFSortChecker.OUTPUT_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == "test"

    def test_locals_pattern_matches(self):
        """Test LOCALS_PATTERN matches locals blocks."""
        content = "locals {"
        match = TFSortChecker.LOCALS_PATTERN.search(content)
        assert match is not None

    def test_locals_pattern_with_whitespace(self):
        """Test LOCALS_PATTERN matches with various whitespace."""
        content = "  locals  {"
        match = TFSortChecker.LOCALS_PATTERN.search(content)
        assert match is not None

    def test_terraform_pattern_matches(self):
        """Test TERRAFORM_PATTERN matches terraform blocks."""
        content = "terraform {"
        match = TFSortChecker.TERRAFORM_PATTERN.search(content)
        assert match is not None

    def test_terraform_pattern_with_whitespace(self):
        """Test TERRAFORM_PATTERN matches with various whitespace."""
        content = "  terraform  {"
        match = TFSortChecker.TERRAFORM_PATTERN.search(content)
        assert match is not None


class TestErrorMessages:
    """Test suite for error message formatting."""

    def test_error_message_contains_expected_order(self, tmp_path):
        """Test error message shows current vs expected order."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text('variable "zzz" {}\nvariable "aaa" {}')

        checker = TFSortChecker([str(test_file)])
        checker.check_file(str(test_file))

        assert len(checker.errors) > 0
        error_msg = checker.errors[0][2]
        assert "Current order:" in error_msg
        assert "Expected order:" in error_msg

    def test_error_message_contains_fix_suggestion(self, tmp_path):
        """Test error message suggests fix using tfsort."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text('variable "zzz" {}\nvariable "aaa" {}')

        checker = TFSortChecker([str(test_file)])
        checker.check_file(str(test_file))

        assert len(checker.errors) > 0
        error_msg = checker.errors[0][2]
        assert "tfsort" in error_msg

    def test_error_message_shows_line_number(self, tmp_path):
        """Test error message includes line number."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text('variable "zzz" {}\nvariable "aaa" {}')

        checker = TFSortChecker([str(test_file)])
        checker.check_file(str(test_file))

        assert len(checker.errors) > 0
        line_num = checker.errors[0][1]
        assert line_num > 0


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_deeply_nested_blocks(self):
        """Test find_block_end with deeply nested blocks."""
        content = (
            'variable "test" {\n  validation {\n    condition = {\n      '
            "nested = true\n    }\n  }\n}"
        )
        start_pos = content.index("{")
        end_pos = TFSortChecker.find_block_end(content, start_pos)
        assert content[end_pos] == "}"

    def test_blocks_with_multiline_strings(self, tmp_path):
        """Test check_file handles blocks with multiline strings."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text(
            """
variable "aaa" {
  description = <<-EOT
    This is a
    multiline description
  EOT
}

variable "bbb" {
  type = string
}
"""
        )

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True

    def test_blocks_with_heredoc(self, tmp_path):
        """Test check_file handles blocks with heredoc syntax."""
        test_file = tmp_path / "outputs.tf"
        test_file.write_text(
            """
output "aaa" {
  value = <<EOF
Content here
EOF
}

output "bbb" {
  value = "simple"
}
"""
        )

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True

    def test_unicode_in_block_names(self, tmp_path):
        """Test check_file handles unicode characters in block names."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text(
            """
variable "aaa_cafe" {
  type = string
}

variable "bbb_naive" {
  type = string
}
""",
            encoding="utf-8",
        )

        checker = TFSortChecker([str(test_file)])
        result = checker.check_file(str(test_file))
        assert result is True


class TestTfsortBinaryIntegration:
    """Test suite for tfsort binary integration."""

    def test_init_with_use_tfsort_binary_flag(self):
        """Test initialization with use_tfsort_binary flag."""
        checker = TFSortChecker(["test.tf"], use_tfsort_binary=True)
        assert checker.use_tfsort_binary is True

        checker2 = TFSortChecker(["test.tf"], use_tfsort_binary=False)
        assert checker2.use_tfsort_binary is False

    def test_find_tfsort_not_installed(self):
        """Test _find_tfsort when tfsort is not installed."""
        with patch("shutil.which", return_value=None):
            checker = TFSortChecker(["test.tf"])
            result = checker._find_tfsort()
            assert result is None
            # Should be cached
            assert checker._tfsort_checked is True
            assert checker._tfsort_path is None

    def test_find_tfsort_installed(self):
        """Test _find_tfsort when tfsort is installed."""
        with patch("shutil.which", return_value="/usr/local/bin/tfsort"):
            checker = TFSortChecker(["test.tf"])
            result = checker._find_tfsort()
            assert result == "/usr/local/bin/tfsort"
            assert checker._tfsort_checked is True
            assert checker._tfsort_path == "/usr/local/bin/tfsort"

    def test_find_tfsort_caching(self):
        """Test _find_tfsort caches the result."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/tfsort"
            checker = TFSortChecker(["test.tf"])

            # First call
            result1 = checker._find_tfsort()
            # Second call
            result2 = checker._find_tfsort()

            # Should only be called once due to caching
            assert mock_which.call_count == 1
            assert result1 == result2

    def test_check_with_tfsort_binary_disabled(self):
        """Test _check_with_tfsort_binary when disabled."""
        checker = TFSortChecker(["test.tf"], use_tfsort_binary=False)
        result = checker._check_with_tfsort_binary("test.tf")
        assert result is None

    def test_check_with_tfsort_binary_not_installed(self, tmp_path):
        """Test _check_with_tfsort_binary when tfsort is not installed."""
        test_file = tmp_path / "test.tf"
        test_file.write_text('variable "aaa" {}')

        with patch("shutil.which", return_value=None):
            checker = TFSortChecker([str(test_file)])
            result = checker._check_with_tfsort_binary(str(test_file))
            assert result is None

    def test_check_with_tfsort_binary_file_sorted(self, tmp_path):
        """Test _check_with_tfsort_binary when file is sorted."""
        test_file = tmp_path / "test.tf"
        content = 'variable "aaa" {}\nvariable "bbb" {}'
        test_file.write_text(content)

        # Mock tfsort to return the same content (file is sorted)
        with patch("shutil.which", return_value="/usr/local/bin/tfsort"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = content

                checker = TFSortChecker([str(test_file)])
                result = checker._check_with_tfsort_binary(str(test_file))

                assert result is not None
                is_sorted, diff_output = result
                assert is_sorted is True
                assert diff_output == ""

    def test_check_with_tfsort_binary_file_unsorted(self, tmp_path):
        """Test _check_with_tfsort_binary when file is unsorted."""
        test_file = tmp_path / "test.tf"
        original_content = 'variable "zzz" {}\nvariable "aaa" {}'
        sorted_content = 'variable "aaa" {}\nvariable "zzz" {}'
        test_file.write_text(original_content)

        with patch("shutil.which", return_value="/usr/local/bin/tfsort"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = sorted_content

                checker = TFSortChecker([str(test_file)])
                result = checker._check_with_tfsort_binary(str(test_file))

                assert result is not None
                is_sorted, diff_output = result
                assert is_sorted is False
                assert len(diff_output) > 0

    def test_check_with_tfsort_binary_subprocess_error(self, tmp_path):
        """Test _check_with_tfsort_binary handles subprocess errors."""
        test_file = tmp_path / "test.tf"
        test_file.write_text('variable "aaa" {}')

        import subprocess

        with patch("shutil.which", return_value="/usr/local/bin/tfsort"):
            with patch("subprocess.run", side_effect=subprocess.SubprocessError):
                checker = TFSortChecker([str(test_file)])
                result = checker._check_with_tfsort_binary(str(test_file))
                assert result is None

    def test_check_with_tfsort_binary_timeout(self, tmp_path):
        """Test _check_with_tfsort_binary handles timeout."""
        test_file = tmp_path / "test.tf"
        test_file.write_text('variable "aaa" {}')

        import subprocess

        with patch("shutil.which", return_value="/usr/local/bin/tfsort"):
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("tfsort", 30)):
                checker = TFSortChecker([str(test_file)])
                result = checker._check_with_tfsort_binary(str(test_file))
                assert result is None

    def test_check_with_tfsort_binary_nonzero_exit(self, tmp_path):
        """Test _check_with_tfsort_binary handles non-zero exit code."""
        test_file = tmp_path / "test.tf"
        test_file.write_text('variable "aaa" {}')

        with patch("shutil.which", return_value="/usr/local/bin/tfsort"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stdout = ""

                checker = TFSortChecker([str(test_file)])
                result = checker._check_with_tfsort_binary(str(test_file))
                # Non-zero exit should cause fallback
                assert result is None

    def test_check_file_uses_tfsort_binary_when_available(self, tmp_path):
        """Test check_file uses tfsort binary when available."""
        test_file = tmp_path / "test.tf"
        content = 'variable "aaa" {}'
        test_file.write_text(content)

        with patch("shutil.which", return_value="/usr/local/bin/tfsort"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = content

                checker = TFSortChecker([str(test_file)])
                result = checker.check_file(str(test_file))

                assert result is True
                mock_run.assert_called_once()

    def test_check_file_falls_back_to_builtin(self, tmp_path):
        """Test check_file falls back to builtin when tfsort not available."""
        test_file = tmp_path / "variables.tf"
        test_file.write_text('variable "aaa" {}\nvariable "bbb" {}')

        with patch("shutil.which", return_value=None):
            checker = TFSortChecker([str(test_file)])
            result = checker.check_file(str(test_file))

            assert result is True

    def test_run_shows_mode_with_tfsort(self, tmp_path, capsys):
        """Test run shows mode message when using tfsort binary."""
        test_file = tmp_path / "test.tf"
        content = 'variable "aaa" {}'
        test_file.write_text(content)

        with patch("shutil.which", return_value="/usr/local/bin/tfsort"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = content

                checker = TFSortChecker([str(test_file)])
                checker.run()

                captured = capsys.readouterr()
                assert "Using tfsort binary" in captured.out

    def test_run_shows_mode_without_tfsort(self, tmp_path, capsys):
        """Test run shows mode message when tfsort not available."""
        test_file = tmp_path / "test.tf"
        test_file.write_text('variable "aaa" {}')

        with patch("shutil.which", return_value=None):
            checker = TFSortChecker([str(test_file)])
            checker.run()

            captured = capsys.readouterr()
            assert "Using built-in block order checking" in captured.out

    def test_main_with_no_tfsort_binary_flag(self, tmp_path):
        """Test main with --no-tfsort-binary flag."""
        test_file = tmp_path / "test.tf"
        test_file.write_text('variable "aaa" {}')

        with patch("sys.argv", ["check_tfsort.py", "--no-tfsort-binary", str(test_file)]):
            with patch("shutil.which", return_value="/usr/local/bin/tfsort") as mock_which:
                result = main()
                # With --no-tfsort-binary, shutil.which should not be called
                mock_which.assert_not_called()
                assert result == 0
