"""
Comprehensive unit tests for check_tofu_integration_tests.py module.

Tests cover all major code paths and edge cases to ensure >80% code coverage.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

from check_tofu_integration_tests import (
    find_integration_test_directory,
    main,
    run_tofu_integration_test,
)

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Monkey patch to prevent stdout/stderr wrapping issues in tests

# Save original stdout/stderr
_orig_stdout = sys.stdout
_orig_stderr = sys.stderr

# Restore original stdout/stderr for tests
sys.stdout = _orig_stdout
sys.stderr = _orig_stderr


class TestFindIntegrationTestDirectory:
    """Test suite for find_integration_test_directory function."""

    def test_find_integration_tests_directory(self, tmp_path, monkeypatch):
        """Test finding 'integration_tests' directory."""
        integration_dir = tmp_path / "integration_tests"
        integration_dir.mkdir()
        (integration_dir / "test.tf").write_text("# test")

        monkeypatch.chdir(tmp_path)
        result = find_integration_test_directory()
        assert result == integration_dir

    def test_find_integration_directory(self, tmp_path, monkeypatch):
        """Test finding 'integration' directory."""
        integration_dir = tmp_path / "integration"
        integration_dir.mkdir()
        (integration_dir / "test.tf").write_text("# test")

        monkeypatch.chdir(tmp_path)
        result = find_integration_test_directory()
        assert result == integration_dir

    def test_find_tests_integration_directory(self, tmp_path, monkeypatch):
        """Test finding 'tests/integration' directory."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        integration_dir = tests_dir / "integration"
        integration_dir.mkdir(parents=True)
        (integration_dir / "test.tf").write_text("# test")

        monkeypatch.chdir(tmp_path)
        result = find_integration_test_directory()
        assert result == integration_dir

    def test_find_test_integration_directory(self, tmp_path, monkeypatch):
        """Test finding 'test/integration' directory."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        integration_dir = test_dir / "integration"
        integration_dir.mkdir(parents=True)
        (integration_dir / "test.tf").write_text("# test")

        monkeypatch.chdir(tmp_path)
        result = find_integration_test_directory()
        assert result == integration_dir

    def test_find_directory_with_integration_in_name(self, tmp_path, monkeypatch):
        """Test finding directory with 'integration' in name."""
        custom_integration_dir = tmp_path / "my_integration_tests"
        custom_integration_dir.mkdir()
        (custom_integration_dir / "test.tf").write_text("# test")

        monkeypatch.chdir(tmp_path)
        result = find_integration_test_directory()
        assert result == custom_integration_dir

    def test_find_integration_test_directory_not_found(self, tmp_path, monkeypatch):
        """Test when no integration test directory is found."""
        monkeypatch.chdir(tmp_path)
        result = find_integration_test_directory()
        assert result is None

    def test_find_integration_directory_no_tf_files(self, tmp_path, monkeypatch):
        """Test integration directory without .tf files is not found."""
        integration_dir = tmp_path / "integration_tests"
        integration_dir.mkdir()
        (integration_dir / "readme.md").write_text("# readme")

        monkeypatch.chdir(tmp_path)
        result = find_integration_test_directory()
        assert result is None

    def test_find_integration_directory_prefers_integration_tests(self, tmp_path, monkeypatch):
        """Test that 'integration_tests' is preferred."""
        integration_tests_dir = tmp_path / "integration_tests"
        integration_tests_dir.mkdir()
        (integration_tests_dir / "test1.tf").write_text("# test")

        integration_dir = tmp_path / "integration"
        integration_dir.mkdir()
        (integration_dir / "test2.tf").write_text("# test")

        monkeypatch.chdir(tmp_path)
        result = find_integration_test_directory()
        assert result == integration_tests_dir

    def test_find_integration_case_insensitive(self, tmp_path, monkeypatch):
        """Test finding directory with INTEGRATION in uppercase."""
        custom_dir = tmp_path / "INTEGRATION_TESTS"
        custom_dir.mkdir()
        (custom_dir / "test.tf").write_text("# test")

        monkeypatch.chdir(tmp_path)
        result = find_integration_test_directory()
        assert result == custom_dir


class TestRunTofuIntegrationTest:
    """Test suite for run_tofu_integration_test function."""

    def test_run_integration_test_success_with_tofu(self, tmp_path, capsys):
        """Test successful integration test run with tofu command."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        mock_result = Mock()
        mock_result.returncode = 0

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), mock_result]
            result = run_tofu_integration_test(test_dir)

        assert result == 0
        captured = capsys.readouterr()
        assert "All TOFU integration tests passed" in captured.out

    def test_run_integration_test_success_with_terraform(self, tmp_path):
        """Test successful integration test with terraform when tofu not available."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        mock_test_result = Mock()
        mock_test_result.returncode = 0

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=1),  # tofu version check fails
                Mock(returncode=0),  # terraform version check succeeds
                mock_test_result,  # terraform test runs
            ]
            result = run_tofu_integration_test(test_dir)

        assert result == 0

    def test_run_integration_test_failure(self, tmp_path, capsys):
        """Test integration test run with failing tests."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        mock_result = Mock()
        mock_result.returncode = 1

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), mock_result]
            result = run_tofu_integration_test(test_dir)

        assert result == 1
        captured = capsys.readouterr()
        assert "integration tests failed" in captured.out

    def test_run_integration_test_command_not_found(self, tmp_path, capsys):
        """Test when neither tofu nor terraform is available."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=1), Mock(returncode=1)]
            result = run_tofu_integration_test(test_dir)

        assert result == 1
        captured = capsys.readouterr()
        assert "Neither 'tofu' nor 'terraform' command found" in captured.out

    def test_run_integration_test_file_not_found_exception(self, tmp_path):
        """Test FileNotFoundError when command doesn't exist."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [FileNotFoundError(), FileNotFoundError()]
            result = run_tofu_integration_test(test_dir)

        assert result == 1

    def test_run_integration_test_verbose(self, tmp_path):
        """Test integration test run with verbose flag."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        mock_result = Mock()
        mock_result.returncode = 0

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), mock_result]
            result = run_tofu_integration_test(test_dir, verbose=True)

        assert result == 0
        # Check that -verbose flag was passed
        test_call_args = mock_run.call_args_list[1]
        assert "-verbose" in test_call_args[0][0]

    def test_run_integration_test_specific_command(self, tmp_path):
        """Test integration test run with specific command."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        mock_result = Mock()
        mock_result.returncode = 0

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), mock_result]
            result = run_tofu_integration_test(test_dir, command="terraform")

        assert result == 0
        # Check that terraform was used
        version_call_args = mock_run.call_args_list[0]
        assert version_call_args[0][0][0] == "terraform"

    def test_run_integration_test_specific_command_not_found(self, tmp_path, capsys):
        """Test when specified command is not found."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)
            result = run_tofu_integration_test(test_dir, command="tofu")

        assert result == 1
        captured = capsys.readouterr()
        assert "'tofu' command not found" in captured.out

    def test_run_integration_test_specific_command_file_not_found(self, tmp_path, capsys):
        """Test FileNotFoundError with specific command."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = run_tofu_integration_test(test_dir, command="tofu")

        assert result == 1


class TestMain:
    """Test suite for main() function."""

    def test_main_auto_detect_success(self, tmp_path, monkeypatch):
        """Test main with auto-detected integration test directory."""
        integration_dir = tmp_path / "integration_tests"
        integration_dir.mkdir()
        (integration_dir / "test.tf").write_text("# test")

        monkeypatch.chdir(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), Mock(returncode=0)]
            result = main([])

        assert result == 0

    def test_main_auto_detect_not_found(self, tmp_path, monkeypatch, capsys):
        """Test main when integration test directory cannot be auto-detected."""
        monkeypatch.chdir(tmp_path)
        result = main([])

        assert result == 1
        captured = capsys.readouterr()
        assert "Could not auto-detect integration test directory" in captured.out

    def test_main_with_test_dir_argument(self, tmp_path):
        """Test main with --test-dir argument."""
        test_dir = tmp_path / "custom_integration"
        test_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), Mock(returncode=0)]
            result = main(["--test-dir", str(test_dir)])

        assert result == 0

    def test_main_test_dir_not_exists(self, tmp_path, capsys):
        """Test main with non-existent test directory."""
        result = main(["--test-dir", str(tmp_path / "nonexistent")])

        assert result == 1
        captured = capsys.readouterr()
        assert "Integration test directory not found" in captured.out

    def test_main_test_dir_not_directory(self, tmp_path, capsys):
        """Test main with test-dir pointing to a file."""
        test_file = tmp_path / "test.tf"
        test_file.write_text("# test")

        result = main(["--test-dir", str(test_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Not a directory" in captured.out

    def test_main_with_verbose(self, tmp_path):
        """Test main with --verbose flag."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), Mock(returncode=0)]
            result = main(["--test-dir", str(test_dir), "--verbose"])

        assert result == 0

    def test_main_with_command_tofu(self, tmp_path):
        """Test main with --command=tofu."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), Mock(returncode=0)]
            result = main(["--test-dir", str(test_dir), "--command", "tofu"])

        assert result == 0

    def test_main_with_command_terraform(self, tmp_path):
        """Test main with --command=terraform."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), Mock(returncode=0)]
            result = main(["--test-dir", str(test_dir), "--command", "terraform"])

        assert result == 0

    def test_main_test_failure(self, tmp_path):
        """Test main when tests fail."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), Mock(returncode=1)]
            result = main(["--test-dir", str(test_dir)])

        assert result == 1

    def test_main_combined_arguments(self, tmp_path):
        """Test main with multiple arguments combined."""
        test_dir = tmp_path / "integration_tests"
        test_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=0), Mock(returncode=0)]
            result = main(
                [
                    "--test-dir",
                    str(test_dir),
                    "--verbose",
                    "--command",
                    "terraform",
                ]
            )

        assert result == 0
