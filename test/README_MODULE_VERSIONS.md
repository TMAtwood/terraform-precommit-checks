# Module Version Checker Tests

Comprehensive test suite for the `check_module_versions.py` pre-commit hook.

## Test Files Overview

### Conflict Detection Tests (Should FAIL)

#### 1. `test_module_conflicts.tf`
Basic module version conflicts across different module types:
- **Registry modules**: Same module with different versions (1.0.0 vs 2.0.0)
- **Git modules**: Same module with different refs (v1.0.0 vs v2.0.0)
- **Commit hashes**: Same module with different commits (abc123 vs xyz789)

**Expected Result**: ❌ 3 conflicts detected

```bash
python check_module_versions.py test/test_module_conflicts.tf
```

#### 2. `test_module_git_conflicts.tf`
Git-specific version conflicts:
- Different commit hashes
- Different tags
- Different refs
- Git URLs with subdirectories
- Multiple git protocols (https, git@, gitlab)

**Expected Result**: ❌ 4 conflicts detected

```bash
python check_module_versions.py test/test_module_git_conflicts.tf
```

#### 3. `test_module_registry_conflicts.tf`
Terraform Registry module conflicts:
- AWS modules (terraform-aws-modules)
- Azure modules (Azure/)
- GCP modules (terraform-google-modules)
- Private registries (app.terraform.io)
- Missing version vs specified version

**Expected Result**: ❌ 5 conflicts detected

```bash
python check_module_versions.py test/test_module_registry_conflicts.tf
```

### Passing Tests (Should PASS)

#### 4. `test_module_consistent.tf`
Consistent module versions:
- Same module called multiple times with identical versions
- Different modules (no conflicts between different modules)
- Local path modules (ignored by checker)

**Expected Result**: ✅ No conflicts

```bash
python check_module_versions.py test/test_module_consistent.tf
```

#### 5. `test_module_mixed_sources.tf`
Mixed module sources without conflicts:
- Multiple different modules from registry (AWS, Azure, GCP)
- Multiple different git modules
- Same modules with consistent versions
- Local modules (properly ignored)

**Expected Result**: ✅ No conflicts (8 modules found, 6 unique)

```bash
python check_module_versions.py test/test_module_mixed_sources.tf -v
```

#### 6. `test_module_edge_cases.tf`
Edge cases and unusual patterns:
- Modules with no version (single reference - OK)
- Branch references
- Bitbucket, GitLab sources
- HTTP module sources
- Private registries
- Complex version constraints
- SSH git URLs
- Terraform Cloud/Enterprise modules

**Expected Result**: ✅ No conflicts (10 unique modules)

```bash
python check_module_versions.py test/test_module_edge_cases.tf -v
```

## Python Unit Tests

### `test_module_versions.py`
Comprehensive Python unit test suite with 26 test cases:

**Unit Tests (21 tests)**:
- Source normalization (registry, git, subdirectories)
- Git ref/tag/commit extraction
- File parsing and module detection
- Conflict detection logic
- Report formatting

**Integration Tests (5 tests)**:
- End-to-end validation using actual test files
- Confirms conflict files fail
- Confirms consistent files pass

**Running Tests**:

```bash
# Run all tests with verbose output
python test/test_module_versions.py -v

# Run specific test class
python test/test_module_versions.py TestModuleVersionChecker -v

# Run integration tests only
python test/test_module_versions.py TestModuleVersionCheckerIntegration -v
```

**Expected Result**: ✅ All 26 tests pass

## Test Coverage

### Module Source Types Tested

| Type | Example | Tested |
|------|---------|--------|
| Registry (Public) | `terraform-aws-modules/vpc/aws` | ✅ |
| Registry (Azure) | `Azure/network/azurerm` | ✅ |
| Registry (GCP) | `terraform-google-modules/network/google` | ✅ |
| Registry (Private) | `app.terraform.io/org/module/provider` | ✅ |
| Git HTTPS | `git::https://github.com/org/repo.git` | ✅ |
| Git SSH | `git::git@github.com:org/repo.git` | ✅ |
| Git with ref | `?ref=v1.0.0` | ✅ |
| Git with tag | `?tag=v2.0.0` | ✅ |
| Git with commit | `?commit=abc123` | ✅ |
| Git with subdirectory | `//modules/compute?ref=v1.0.0` | ✅ |
| Local relative | `./modules/helper` | ✅ (ignored) |
| Local parent | `../shared-modules/compute` | ✅ (ignored) |
| HTTP archive | `https://example.com/module.zip` | ✅ |
| Bitbucket | `git::https://bitbucket.org/...` | ✅ |
| GitLab | `git::https://gitlab.com/...` | ✅ |

### Conflict Scenarios Tested

| Scenario | Test File | Status |
|----------|-----------|--------|
| Different registry versions | `test_module_registry_conflicts.tf` | ✅ |
| Different git refs | `test_module_git_conflicts.tf` | ✅ |
| Different git tags | `test_module_git_conflicts.tf` | ✅ |
| Different commit hashes | `test_module_conflicts.tf` | ✅ |
| Version vs no version | `test_module_registry_conflicts.tf` | ✅ |
| Same version (consistent) | `test_module_consistent.tf` | ✅ |
| Different modules (no conflict) | `test_module_mixed_sources.tf` | ✅ |
| Git subdirectory conflicts | `test_module_git_conflicts.tf` | ✅ |

### Edge Cases Tested

| Edge Case | Handled |
|-----------|---------|
| Non-existent files | ✅ |
| Malformed HCL | ✅ |
| Modules with no source | ✅ |
| Local path modules | ✅ (skipped) |
| Multiple query parameters | ✅ |
| Trailing slashes in source | ✅ |
| Different git protocols (git::, https::) | ✅ |
| Branch references | ✅ |
| Complex version constraints | ✅ |

## Running All Tests

### Via Python

```bash
# Run Python unit tests
python test/test_module_versions.py -v

# Run hook on all test files
python check_module_versions.py test/test_module_*.tf
```

### Via Pre-commit

```bash
# Run on all .tf files
pre-commit run check-module-versions --all-files

# Run on specific files
pre-commit run check-module-versions --files test/test_module_conflicts.tf
```

### Via pytest (if installed)

```bash
# Run with pytest
pytest test/test_module_versions.py -v

# Run with coverage
pytest test/test_module_versions.py --cov=check_module_versions --cov-report=term-missing
```

## Expected Outcomes Summary

| Test File | Expected Outcome | Conflicts |
|-----------|------------------|-----------|
| `test_module_conflicts.tf` | ❌ FAIL | 3 |
| `test_module_git_conflicts.tf` | ❌ FAIL | 4 |
| `test_module_registry_conflicts.tf` | ❌ FAIL | 5 |
| `test_module_consistent.tf` | ✅ PASS | 0 |
| `test_module_mixed_sources.tf` | ✅ PASS | 0 |
| `test_module_edge_cases.tf` | ✅ PASS | 0 |
| `test_module_versions.py` | ✅ PASS | 26/26 tests |

## Understanding Test Output

### Conflict Detected (Expected Failure)

```
================================================================================
❌ MODULE VERSION CONFLICTS DETECTED
================================================================================

📦 Module: terraform-aws-modules/vpc/aws
   Conflicting references:

   📁 File: test/test_module_conflicts.tf
   📍 Line: 5
   🔖 Version: version = 1.0.0
   🔗 Source: terraform-aws-modules/vpc/aws

   📁 File: test/test_module_conflicts.tf
   📍 Line: 14
   🔖 Version: version = 2.0.0
   🔗 Source: terraform-aws-modules/vpc/aws

   ⚠️  Resolution:
   All references to this module should use the same version/ref.
   Choose one version and update all references to match.
```

### No Conflicts (Expected Pass)

```
✓ Scanned 1 files
✓ Found 8 module references
✓ Checking 6 unique modules

✅ No module version conflicts detected!
```

## Test Maintenance

### Adding New Test Cases

1. **Create test file**: Add new `.tf` file in `test/` directory
2. **Add test case**: Add corresponding test in `test_module_versions.py`
3. **Document**: Update this README with expected outcomes
4. **Verify**: Run tests to confirm behavior

### Modifying Existing Tests

1. Update the `.tf` test file
2. Update corresponding Python test assertions
3. Re-run full test suite
4. Update documentation if behavior changes

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Test Module Version Checker
  run: |
    python test/test_module_versions.py
    python check_module_versions.py test/test_module_*.tf || true
```

```bash
# Example GitLab CI
test_module_versions:
  script:
    - python test/test_module_versions.py
    - python check_module_versions.py test/test_module_*.tf || true
```

## Troubleshooting

### Issue: Unicode errors on Windows

**Solution**: Already fixed with UTF-8 encoding in script header

### Issue: Tests fail due to missing files

**Solution**: Ensure you're running from repository root:
```bash
cd /path/to/terraform-provider-convention-checker
python test/test_module_versions.py
```

### Issue: False positives

**Solution**: Check that module sources are correctly normalized. Local paths should be skipped.

## References

- Main hook: [check_module_versions.py](../check_module_versions.py)
- Configuration: [.pre-commit-config.yaml](../.pre-commit-config.yaml)
- Documentation: [CLAUDE.md](../CLAUDE.md)
