# Terraform/OpenTofu Test Examples

This directory contains example test files for the `check-tofu-unit-tests` and `check-tofu-integration-tests` pre-commit hooks.

## Directory Structure

```
tests/
├── unit/                   # Unit tests
│   ├── main.tf            # Simple variable and validation tests
│   └── main.tftest.hcl    # Unit test assertions
└── integration/            # Integration tests
    ├── main.tf            # Resource creation and interaction tests
    └── main.tftest.hcl    # Integration test assertions
```

## Unit Tests (`tests/unit/`)

Unit tests validate basic functionality without external dependencies:

- **Variable validation**: Tests that variables have correct defaults and validation rules
- **Output verification**: Ensures outputs match expected values
- **Type checking**: Validates variable types (string, number, list)

### Running Unit Tests

```bash
# Auto-detect test directory
python check_tofu_unit_tests.py

# Specify custom directory
python check_tofu_unit_tests.py --test-dir=tests/unit

# Via pre-commit (manual stage)
pre-commit run check-tofu-unit-tests --hook-stage manual
```

### Example Test Output

```
✓ Scanned tests/unit
✓ Found 5 test cases
✅ All TOFU unit tests passed!
```

## Integration Tests (`tests/integration/`)

Integration tests validate more complex scenarios with resource interactions:

- **Resource creation**: Tests creating multiple resources with `count`
- **Output relationships**: Validates outputs derived from resources
- **Local values**: Tests computed local values based on resources
- **Environment simulation**: Tests different environment configurations

### Running Integration Tests

```bash
# Auto-detect integration test directory
python check_tofu_integration_tests.py

# Specify custom directory
python check_tofu_integration_tests.py --test-dir=tests/integration

# Via pre-commit (manual stage)
pre-commit run check-tofu-integration-tests --hook-stage manual
```

### Example Test Output

```
✓ Scanned tests/integration
✓ Found 7 test cases
✅ All TOFU integration tests passed!
```

## Test File Format

Both unit and integration tests use the Terraform native testing framework (`.tftest.hcl` files):

```hcl
run "test_name" {
  command = plan  # or apply

  variables {
    # Override input variables
    test_var = "value"
  }

  assert {
    condition     = var.test_var == "value"
    error_message = "Should match expected value"
  }
}
```

## Features Demonstrated

### Unit Tests
- ✅ Variable validation rules
- ✅ Default value testing
- ✅ Custom value testing
- ✅ Output verification
- ✅ Type constraints

### Integration Tests
- ✅ Resource creation with `count`
- ✅ Local value computation
- ✅ Resource data access
- ✅ Complex output structures (lists, maps)
- ✅ Multi-variable scenarios
- ✅ Environment-based configuration

## Using These Tests as Templates

You can use these test files as templates for your own Terraform/OpenTofu projects:

1. **Copy the structure**: Use the same directory layout (`tests/unit/`, `tests/integration/`)
2. **Adapt the tests**: Modify `main.tf` and `main.tftest.hcl` for your use case
3. **Run via hooks**: The pre-commit hooks will auto-detect these directories

## Requirements

- **Terraform >= 1.6** or **OpenTofu >= 1.6** (native testing support)
- Tests use `terraform_data` resource (no provider configuration needed)
- Tests run with `command = plan` (no actual infrastructure created)

## Additional Resources

- [Terraform Testing Documentation](https://developer.hashicorp.com/terraform/language/tests)
- [OpenTofu Testing Documentation](https://opentofu.org/docs/language/tests/)
- [Terraform Test Command](https://developer.hashicorp.com/terraform/cli/commands/test)
