#!/usr/bin/env python3
"""
Pre-commit hook to run Terraform/OpenTofu (TOFU) unit tests.

This hook ensures that TOFU tests pass before allowing commits.
It can automatically detect test directories or accept a custom path.
"""

import argparse
import io
import subprocess  # nosec B404
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def find_test_directory() -> Path | None:
    """
    Automatically detect the TOFU test directory.

    Searches for test directories in common patterns including nested structures:
    - tests/
    - test/
    - test/unit/
    - *_test/
    - Any directory containing .tftest.hcl files

    Returns:
        Path to test directory if found, None otherwise.
    """
    current_dir = Path.cwd()

    # Check for .tftest.hcl files in specific locations (most specific first)
    test_locations = [
        current_dir / "test" / "fixture" / "unit_tests",
        current_dir / "test" / "fixture" / "unit",
        current_dir / "test" / "unit",
        current_dir / "tests" / "unit",
        current_dir / "test",
        current_dir / "tests",
    ]

    for test_dir in test_locations:
        if test_dir.exists() and test_dir.is_dir():
            # Look for .tftest.hcl files (OpenTofu test marker)
            if list(test_dir.glob("**/*.tftest.hcl")):
                return test_dir
            # Fallback to .tf files
            if list(test_dir.glob("**/*.tf")):
                return test_dir

    # Look for directories ending with _test
    try:
        for path in current_dir.iterdir():
            if (
                path.is_dir()
                and path.name.endswith("_test")
                and (list(path.glob("**/*.tftest.hcl")) or list(path.glob("**/*.tf")))
            ):
                return path
    except (PermissionError, OSError):
        pass

    return None


def get_test_subdirectory(test_dir: Path) -> str | None:
    """
    Detect if test files are in subdirectories and need -test-directory flag.

    Args:
        test_dir: Path to the test directory

    Returns:
        Subdirectory name if needed, None if tests are in root of test_dir
    """
    # Check if .tftest.hcl files are in subdirectories
    test_files = list(test_dir.glob("**/*.tftest.hcl"))
    if test_files:
        # Get the first test file's parent directory relative to test_dir
        first_test_parent = test_files[0].parent
        if first_test_parent != test_dir:
            # Return relative path from test_dir
            return str(first_test_parent.relative_to(test_dir))
    return None


def run_tofu_test(test_dir: Path, verbose: bool = False, command: str | None = None) -> int:
    """
    Run TOFU test command in the specified directory.

    Args:
        test_dir: Path to the test directory
        verbose: Whether to show verbose output
        command: Specific command to use ('tofu' or 'terraform'). If None,
            tries tofu first, then terraform.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print(f"🔍 Running TOFU tests in: {test_dir}")
    print("=" * 80)

    # Determine which commands to try
    commands = [command] if command else ["tofu", "terraform"]

    # Check if tests are in subdirectories
    test_subdir = get_test_subdirectory(test_dir)
    if test_subdir:
        print(f"📂 Tests found in subdirectory: {test_subdir}")

    for cmd in commands:
        try:
            # Check if command exists
            check_cmd = subprocess.run(  # nosec B603 B607
                [cmd, "version"], capture_output=True, text=True, check=False
            )

            if check_cmd.returncode != 0:
                if command:
                    print(f"❌ ERROR: '{cmd}' command not found or not working!")
                    print(f"   Please install {cmd} to run tests.")
                    return 1
                continue

            print(f"✓ Using '{cmd}' command")
            print("")

            # Run the test
            test_args = [cmd, "test"]
            if test_subdir:
                test_args.extend(["-test-directory", test_subdir])
            if verbose:
                test_args.append("-verbose")

            # Run without capturing output so users see full test results
            result = subprocess.run(  # nosec B603 B607
                test_args, cwd=test_dir, check=False
            )

            print("")
            print("=" * 80)

            if result.returncode == 0:
                print("✅ All TOFU tests passed!")
                return 0
            else:
                print(f"❌ TOFU tests failed with exit code: {result.returncode}")
                print("   See output above for details on which tests failed.")
                return result.returncode

        except FileNotFoundError:
            if command:
                print(f"❌ ERROR: '{cmd}' command not found!")
                print(f"   Please install {cmd} to run tests.")
                return 1
            continue

    print("❌ ERROR: Neither 'tofu' nor 'terraform' command found!")
    print("   Please install OpenTofu or Terraform to run tests.")
    return 1


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for the TOFU test checker.

    Args:
        argv: Command line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="Run Terraform/OpenTofu unit tests as a pre-commit hook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect test directory
  python check_tofu_tests.py

  # Specify custom test directory
  python check_tofu_tests.py --test-dir=./my-tests

  # Use OpenTofu specifically
  python check_tofu_tests.py --command=tofu

  # Use Terraform specifically
  python check_tofu_tests.py --command=terraform

  # Verbose output
  python check_tofu_tests.py --verbose
        """,
    )

    parser.add_argument(
        "--test-dir", type=str, help="Path to the test directory (auto-detected if not specified)"
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose test output")

    parser.add_argument(
        "--command",
        type=str,
        choices=["tofu", "terraform"],
        help="Specify which command to use: 'tofu' or 'terraform' (auto-detects if not specified)",
    )

    args = parser.parse_args(argv)

    # Determine test directory
    if args.test_dir:
        test_dir = Path(args.test_dir)
        if not test_dir.exists():
            print(f"❌ ERROR: Test directory not found: {test_dir}")
            return 1
        if not test_dir.is_dir():
            print(f"❌ ERROR: Not a directory: {test_dir}")
            return 1
        print(f"📁 Using specified test directory: {test_dir}")
    else:
        print("🔍 Auto-detecting test directory...")
        test_dir_result = find_test_directory()
        if not test_dir_result:
            print("❌ ERROR: Could not auto-detect test directory!")
            print("   Please specify --test-dir or create a 'tests/' or 'test/' directory")
            return 1
        test_dir = test_dir_result
        print(f"📁 Found test directory: {test_dir}")

    print("")

    # Run the tests
    return run_tofu_test(test_dir, args.verbose, args.command)


if __name__ == "__main__":
    sys.exit(main())
