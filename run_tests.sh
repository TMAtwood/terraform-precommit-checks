#!/usr/bin/env bash
# Convenience script to run all test suites from the root directory

# Use subshell-safe settings (no set -u to avoid issues when sourced)
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================================================"
echo "Running unified test suite"
echo "================================================================================"
echo ""

# Track overall success
OVERALL_EXIT_CODE=0

# Run the legacy unified test suite
echo "📋 Running Legacy Integration Tests (test_hooks.py)"
echo "--------------------------------------------------------------------------------"
cd "$SCRIPT_DIR/test" || return 1
python test_hooks.py
TEST_EXIT_CODE=$?
if [ $TEST_EXIT_CODE -ne 0 ]; then
    OVERALL_EXIT_CODE=$TEST_EXIT_CODE
fi
echo ""

# Run the pytest unit test suite with coverage
echo "📋 Running Pytest Unit Tests with Coverage"
echo "--------------------------------------------------------------------------------"
cd "$SCRIPT_DIR" || return 1
python -m pytest test/test_provider_config.py test/test_module_versions.py test/test_tfsort.py \
    test/test_tofu_unit_tests.py test/test_tofu_integration_tests.py \
    --cov=check_provider_config --cov=check_module_versions --cov=check_tfsort \
    --cov=check_tofu_unit_tests --cov=check_tofu_integration_tests \
    --cov-report=term --cov-report=html -v
TEST_EXIT_CODE=$?
if [ $TEST_EXIT_CODE -ne 0 ]; then
    OVERALL_EXIT_CODE=$TEST_EXIT_CODE
fi
echo ""

# Show overall result
echo "================================================================================"
if [ $OVERALL_EXIT_CODE -eq 0 ]; then
    echo "✅ All test suites completed successfully"
else
    echo "❌ Some tests failed with exit code: $OVERALL_EXIT_CODE"
fi
echo "================================================================================"

# Return to original directory
cd "$SCRIPT_DIR" || return 1

# Restore original shell options if sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Disable pipefail to not affect interactive shell
    set +o pipefail 2>/dev/null || true
    # Disable nounset (set -u) if it was set by this script or previous context
    set +u 2>/dev/null || true
    return $OVERALL_EXIT_CODE
fi

# Only exit if not sourced - allows return to WSL prompt
exit $OVERALL_EXIT_CODE
