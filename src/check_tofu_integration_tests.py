#!/usr/bin/env python3
"""
Pre-commit hook to run Terraform/OpenTofu (TOFU) integration tests.

This hook ensures that TOFU integration tests pass before allowing commits.
It can automatically detect integration test directories or accept a custom path.
"""

import argparse
import io
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import List, Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def find_integration_test_directory() -> Optional[Path]:
    """
    Automatically detect the TOFU integration test directory.

    Common patterns:
    - integration_tests/
    - integration/
    - tests/integration/
    - test/integration/

    Returns:
        Path to integration test directory if found, None otherwise.
    """
    current_dir = Path.cwd()

    # Check common integration test directory names
    common_names = [
        "integration_tests",
        "integration",
        "tests/integration",
        "test/integration",
    ]
    for name in common_names:
        test_dir = current_dir / name
        if test_dir.exists() and test_dir.is_dir() and list(test_dir.glob("**/*.tf")):
            return test_dir

    # Look for directories containing "integration"
    for path in current_dir.iterdir():
        if path.is_dir() and "integration" in path.name.lower() and list(path.glob("**/*.tf")):
            return path

    return None


def run_tofu_integration_test(
    test_dir: Path, verbose: bool = False, command: Optional[str] = None
) -> int:
    """Run TOFU integration test command in the specified directory.

    Args:
        test_dir: Path to the integration test directory
        verbose: Whether to show verbose output
        command: Specific command to use ('tofu' or 'terraform'). If None,
            tries tofu first, then terraform.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print(f"🔍 Running TOFU integration tests in: {test_dir}")
    print("=" * 80)

    # Determine which commands to try
    commands = [command] if command else ["tofu", "terraform"]

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
            if verbose:
                test_args.append("-verbose")

            # Run without capturing output so users see full test results
            result = subprocess.run(  # nosec B603 B607
                test_args, cwd=test_dir, check=False
            )

            print("")
            print("=" * 80)

            if result.returncode == 0:
                print("✅ All TOFU integration tests passed!")
                return 0
            else:
                print(f"❌ TOFU integration tests failed with exit code: {result.returncode}")
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


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the TOFU integration test checker.

    Args:
        argv: Command line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="Run Terraform/OpenTofu integration tests as a pre-commit hook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect integration test directory
  python check_tofu_integration_tests.py

  # Specify custom integration test directory
  python check_tofu_integration_tests.py --test-dir=./integration

  # Use OpenTofu specifically
  python check_tofu_integration_tests.py --command=tofu

  # Use Terraform specifically
  python check_tofu_integration_tests.py --command=terraform

  # Verbose output
  python check_tofu_integration_tests.py --verbose
        """,
    )

    parser.add_argument(
        "--test-dir",
        type=str,
        help="Path to the integration test directory (auto-detected if not specified)",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose test output")

    parser.add_argument(
        "--command",
        type=str,
        choices=["tofu", "terraform"],
        help="Specify which command to use: 'tofu' or 'terraform' (auto-detects if not specified)",
    )

    args = parser.parse_args(argv)

    # Determine integration test directory
    if args.test_dir:
        test_dir = Path(args.test_dir)
        if not test_dir.exists():
            print(f"❌ ERROR: Integration test directory not found: {test_dir}")
            return 1
        if not test_dir.is_dir():
            print(f"❌ ERROR: Not a directory: {test_dir}")
            return 1
        print(f"📁 Using specified integration test directory: {test_dir}")
    else:
        print("🔍 Auto-detecting integration test directory...")
        test_dir_result = find_integration_test_directory()
        if not test_dir_result:
            print("❌ ERROR: Could not auto-detect integration test directory!")
            print(
                "   Please specify --test-dir or create an 'integration_tests/',"
                " 'integration/', or similar directory"
            )
            return 1
        test_dir = test_dir_result
        print(f"📁 Found integration test directory: {test_dir}")

    print("")

    # Run the integration tests
    return run_tofu_integration_test(test_dir, args.verbose, args.command)


if __name__ == "__main__":
    sys.exit(main())
