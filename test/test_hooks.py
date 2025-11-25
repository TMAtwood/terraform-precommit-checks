"""
Unified test suite for all pre-commit hooks.

Tests:
- Provider configuration checker (check_provider_config.py)
- TFSort checker (check_tfsort.py)
- Module version checker (check_module_versions.py)
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


def run_test(
    test_name: str, file_path: str, should_pass: bool, script_name: str = "check_provider_config.py"
) -> bool:
    """Run a single test case."""
    print(f"\n{'=' * 80}")
    print(f"Testing: {test_name}")
    print(f"{'=' * 80}")

    # Get the path to the checker script (in src directory)
    script_dir = Path(__file__).parent.parent / "src"
    checker_script = script_dir / script_name

    result = subprocess.run(  # nosec B603 B607
        ["python", str(checker_script), file_path], capture_output=True, text=True
    )

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


def run_provider_tests() -> list[bool]:
    """Run provider configuration checker tests."""
    print("\n" + "=" * 80)
    print("RUNNING PROVIDER CONFIGURATION CHECKER TESTS")
    print("=" * 80)

    tests = [
        (
            "AWS old-style provider config (should fail)",
            "test_aws_old.tf",
            False,
            "check_provider_config.py",
        ),
        (
            "AWS new-style provider config (should pass)",
            "test_aws_new.tf",
            True,
            "check_provider_config.py",
        ),
        (
            "Azure old-style provider config (should fail)",
            "test_azure_old.tf",
            False,
            "check_provider_config.py",
        ),
        (
            "Azure new-style provider config (should pass)",
            "test_azure_new.tf",
            True,
            "check_provider_config.py",
        ),
        (
            "GCP old-style provider config (should fail)",
            "test_gcp_old.tf",
            False,
            "check_provider_config.py",
        ),
        (
            "GCP new-style provider config (should pass)",
            "test_gcp_new.tf",
            True,
            "check_provider_config.py",
        ),
        (
            "OCI old-style provider config (should fail)",
            "test_oci_old.tf",
            False,
            "check_provider_config.py",
        ),
        (
            "OCI new-style provider config (should pass)",
            "test_oci_new.tf",
            True,
            "check_provider_config.py",
        ),
    ]

    results = []
    for test_name, file_path, should_pass, script_name in tests:
        if not Path(file_path).exists():
            print(f"⚠️  Skipping {test_name}: {file_path} not found")
            continue
        results.append(run_test(test_name, file_path, should_pass, script_name))

    return results


def run_tfsort_tests() -> list[bool]:
    """Run tfsort checker tests."""
    print("\n" + "=" * 80)
    print("RUNNING TFSORT CHECKER TESTS")
    print("=" * 80)

    tests = [
        (
            "Sorted variables (should pass)",
            "test_tfsort_sorted_variables.tf",
            True,
            "check_tfsort.py",
        ),
        ("Sorted outputs (should pass)", "test_tfsort_sorted_outputs.tf", True, "check_tfsort.py"),
        (
            "Unsorted variables and outputs (should fail)",
            "test_tfsort_unsorted.tf",
            False,
            "check_tfsort.py",
        ),
    ]

    results = []
    for test_name, file_path, should_pass, script_name in tests:
        if not Path(file_path).exists():
            print(f"⚠️  Skipping {test_name}: {file_path} not found")
            continue
        results.append(run_test(test_name, file_path, should_pass, script_name))

    return results


def run_module_version_tests() -> list[bool]:
    """Run module version checker tests."""
    print("\n" + "=" * 80)
    print("RUNNING MODULE VERSION CHECKER TESTS")
    print("=" * 80)

    tests = [
        (
            "Module version conflicts (should fail)",
            "test_module_conflicts.tf",
            False,
            "check_module_versions.py",
        ),
        (
            "Module git ref conflicts (should fail)",
            "test_module_git_conflicts.tf",
            False,
            "check_module_versions.py",
        ),
        (
            "Module registry conflicts (should fail)",
            "test_module_registry_conflicts.tf",
            False,
            "check_module_versions.py",
        ),
        (
            "Consistent module versions (should pass)",
            "test_module_consistent.tf",
            True,
            "check_module_versions.py",
        ),
        (
            "Mixed module sources (should pass)",
            "test_module_mixed_sources.tf",
            True,
            "check_module_versions.py",
        ),
        (
            "Module edge cases (should pass)",
            "test_module_edge_cases.tf",
            True,
            "check_module_versions.py",
        ),
    ]

    results = []
    for test_name, file_path, should_pass, script_name in tests:
        if not Path(file_path).exists():
            print(f"⚠️  Skipping {test_name}: {file_path} not found")
            continue
        results.append(run_test(test_name, file_path, should_pass, script_name))

    return results


def main() -> int:
    """Run all tests."""
    all_results = []

    # Run provider configuration tests
    provider_results = run_provider_tests()
    all_results.extend(provider_results)

    # Run tfsort tests
    tfsort_results = run_tfsort_tests()
    all_results.extend(tfsort_results)

    # Run module version tests
    module_version_results = run_module_version_tests()
    all_results.extend(module_version_results)

    # Print overall summary
    print("\n" + "=" * 80)
    print("OVERALL TEST SUMMARY")
    print("=" * 80)
    print(f"Total Passed: {sum(all_results)}/{len(all_results)}")
    print(f"Total Failed: {len(all_results) - sum(all_results)}/{len(all_results)}")
    print()
    print(f"Provider Config Tests: {sum(provider_results)}/{len(provider_results)} passed")
    print(f"TFSort Tests: {sum(tfsort_results)}/{len(tfsort_results)} passed")
    print(
        f"Module Version Tests: {sum(module_version_results)}/{len(module_version_results)} passed"
    )

    if all(all_results):
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
