"""
Test suite for Terraform tag validation hook.

Tests the check_terraform_tags.py hook with various scenarios.
"""

import subprocess  # nosec B404
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure output encoding for Windows console
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def run_tag_test(
    test_name: str,
    file_path: str,
    should_pass: bool,
    config_file: str = ".terraform-tags-test.yaml",
) -> bool:
    """Run a single tag validation test case."""
    print(f"\n{'=' * 80}")
    print(f"Testing: {test_name}")
    print(f"{'=' * 80}")

    # Get the paths
    test_dir = Path(__file__).parent
    src_dir = test_dir.parent / "src"
    checker_script = src_dir / "check_terraform_tags.py"
    config_path = test_dir / config_file
    test_file = test_dir / file_path

    # Run the checker
    cmd = ["python", str(checker_script), "--config", str(config_path), str(test_file)]

    result = subprocess.run(cmd, capture_output=True, text=True)  # nosec B603 B607

    passed = (result.returncode == 0) == should_pass

    if passed:
        print(f"✅ PASSED: {test_name}")
    else:
        print(f"❌ FAILED: {test_name}")
        expected = "pass" if should_pass else "fail"
        print(f"Expected to {expected}, but got returncode {result.returncode}")
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

    return passed


def run_tag_tests() -> list:
    """Run all tag validation tests."""
    print("\n" + "=" * 80)
    print("RUNNING TERRAFORM TAG VALIDATION TESTS")
    print("=" * 80)

    tests = [
        (
            "Valid tags - all required tags present (should pass)",
            "test_tags_valid.tf",
            True,
            ".terraform-tags-test.yaml",
        ),
        (
            "Invalid tags - various violations (should fail)",
            "test_tags_invalid.tf",
            False,
            ".terraform-tags-test.yaml",
        ),
        (
            "Valid tags with patterns - patterns match (should pass)",
            "test_tags_patterns_valid.tf",
            True,
            ".terraform-tags-patterns-test.yaml",
        ),
        (
            "Invalid tags with patterns - patterns don't match (should fail)",
            "test_tags_patterns_invalid.tf",
            False,
            ".terraform-tags-patterns-test.yaml",
        ),
    ]

    results = []
    for test_name, file_path, should_pass, config_file in tests:
        passed = run_tag_test(test_name, file_path, should_pass, config_file)
        results.append(passed)

    return results


def main() -> int:
    """Main test runner."""
    print("\n" + "🏷️ " * 20)
    print("TERRAFORM TAG VALIDATION TEST SUITE")
    print("🏷️ " * 20)

    results = run_tag_tests()

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"Total tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
