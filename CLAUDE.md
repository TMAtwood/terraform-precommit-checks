# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **provider-agnostic** pre-commit hook for Terraform/OpenTofu that detects old-style provider configurations which prevent module-level `for_each` and `depends_on` meta-arguments. It works universally with any Terraform provider (AWS, Azure, GCP, Oracle Cloud, and 3,000+ others).

### The Problem Being Solved

When Terraform/OpenTofu modules use direct `provider "name" { }` blocks (old pattern), the Terraform engine prevents using `for_each` and `depends_on` when calling those modules. This hook enforces the new `required_providers` pattern with `configuration_aliases`, which enables these powerful meta-arguments.

## Core Architecture

### Main Components

1. **check_provider_config.py** - Python-based pre-commit hook (executable)
   - Main class: `ProviderConfigChecker`
   - Uses regex patterns to detect old-style `provider "name" { }` blocks
   - Distinguishes between root modules and reusable modules
   - Provides detailed error messages with line numbers and remediation guidance

2. **check_module_versions.py** - Module version consistency checker
   - Main class: `ModuleVersionChecker`
   - Detects conflicting module versions or git refs across all `.tf` files
   - Supports registry modules (with `version`), git modules (with refs/tags/commits)
   - Ensures all references to the same module use consistent versions
   - Provides detailed conflict reports with file locations and line numbers
   - Supports `--exclude-dir` flag to skip checking specific directories
   - Includes Windows UTF-8 handling for proper emoji/unicode output

3. **check_tfsort.py** - Terraform file sorting checker
   - Main class: `TFSortChecker`
   - Verifies variable and output blocks are sorted alphabetically
   - Focuses on `variables.tf` and `outputs.tf` files
   - Provides clear error messages showing current vs. expected order
   - Compatible with tfsort tool for automatic fixes

4. **check_tofu_unit_tests.py** - Terraform/OpenTofu unit test runner
   - Runs `terraform test` or `tofu test` on unit test directories
   - Auto-detects test directories (tests/, test/, *_test/)
   - Tries `tofu` first, then falls back to `terraform` (or use `--command` to specify)
   - Manual stage hook - run with `pre-commit run check-tofu-unit-tests`

5. **check_tofu_integration_tests.py** - Terraform/OpenTofu integration test runner
   - Runs integration tests in dedicated directories
   - Auto-detects integration test paths (integration_tests/, integration/, tests/integration/)
   - Tries `tofu` first, then falls back to `terraform` (or use `--command` to specify)
   - Manual stage hook - run with `pre-commit run check-tofu-integration-tests`

6. **check_terraform_tags.py** - Terraform resource tag validation hook
   - Main class: `TerraformTagChecker`
   - Validates required tags are present on all taggable resources
   - Enforces case-sensitive tag keys and values
   - Supports allowed values lists with case-sensitive validation
   - Works with all providers (AWS tags, Azure tags, GCP labels, etc.)
   - Flexible configuration via YAML file or JSON command-line arguments
   - Includes comprehensive built-in lists of taggable resources for AWS, Azure, GCP, Oracle Cloud

7. **check_template_sync.py** - Repository scaffold file synchronization checker
   - Main class: `TemplateSyncChecker`
   - Validates that repository scaffold files match a reference template directory
   - Uses SHA256 hash comparison to detect file content differences
   - Checks for missing files, missing directories, and content mismatches
   - Supports scaffold files like .editorconfig, .gitignore, .pre-commit-config.yaml, Jenkinsfile, .terraform-tags.yaml
   - Excludes common directories (.git, **pycache**, .terraform, node_modules, etc.)
   - Provides verbose error messages with file paths and hash comparisons
   - Requires `--template-path` argument pointing to reference template directory
   - Manual stage hook - run with `pre-commit run check-template-sync --hook-stage manual`

8. **.pre-commit-config.yaml** - Pre-commit framework configuration (for local development)
   - Defines all local hooks that run on `.tf` files
   - Includes Python quality, security, and testing hooks
   - Can be extended with additional Terraform hooks (terraform_fmt, terraform_validate, etc.)

9. **.pre-commit-hooks.yaml** - Remote hook definitions
   - Defines hooks for remote usage when installed via `repos:` in other projects
   - Specifies hook IDs, entry points, file patterns, and minimum pre-commit version
   - Used when others install this repository as a pre-commit dependency

10. **setup.sh** - Automated installation script (Bash)
    - Checks for prerequisites (pre-commit, git)
    - Copies files and installs hooks
    - Runs initial validation

11. **verify_multi_cloud.sh** - Multi-provider verification script (Bash)
    - Demonstrates provider-agnostic detection across AWS, Azure, GCP, Oracle

12. **create_version_tag.sh** - Version tagging script (Bash)
    - Creates semantic version tags (e.g., v1.0.0)
    - Moves 'latest' tag to the new version
    - Supports GitVersion integration for automatic version detection
    - Validates semantic versioning format
    - Pushes tags to remote repository

### Detection Logic

#### Provider Configuration Checker

The provider checker implements two primary patterns:

1. **PROVIDER_BLOCK_PATTERN**: `r'^\s*provider\s+"([^"]+)"\s*\{'`
   - Detects direct provider blocks (the problematic pattern)

2. **REQUIRED_PROVIDERS_PATTERN**: `r'terraform\s*\{[^}]*required_providers\s*\{'`
   - Detects the correct new-style pattern

**Context-aware filtering**:

- Skips providers inside `required_providers` blocks
- Skips `configuration_aliases` declarations (these are correct)
- Skips mock/test providers
- Uses 500-character lookback for context analysis

**Module detection** (`is_module_directory()`):

- Checks for `variables.tf` or `outputs.tf` in directory
- Checks if path contains 'modules' directory
- Different error messages for modules vs root configurations

#### Module Version Checker

The module version checker detects conflicting versions across module references:

1. **Module Reference Extraction**:
   - Parses all `module` blocks in `.tf` files
   - Extracts `source` and `version` attributes
   - Identifies git refs, tags, and commit hashes from git sources

2. **Source Normalization**:
   - Normalizes module sources by removing version parameters
   - Groups references to the same module for comparison
   - Handles git URLs with different protocols (git::, https::)

3. **Conflict Detection**:
   - Compares all references to the same module
   - Reports conflicts when versions/refs differ
   - Skips local path modules (./modules/..., ../...)

4. **Supported Module Types**:
   - **Registry modules**: `terraform-aws-modules/vpc/aws` with `version = "3.0.0"`
   - **Git with refs**: `git::https://github.com/org/repo.git?ref=v1.0.0`
   - **Git with tags**: `git::https://github.com/org/repo.git?tag=v2.0.0`
   - **Git with commits**: `git::https://github.com/org/repo.git?commit=abc123`

#### TFSort Checker

The tfsort checker verifies alphabetical sorting of Terraform blocks:

1. **Block Detection Patterns**:
   - `VARIABLE_PATTERN`: `r'^\s*variable\s+"([^"]+)"\s*\{'` - Detects variable blocks
   - `OUTPUT_PATTERN`: `r'^\s*output\s+"([^"]+)"\s*\{'` - Detects output blocks
   - `LOCALS_PATTERN`: `r'^\s*locals\s*\{'` - Detects locals blocks
   - `TERRAFORM_PATTERN`: `r'^\s*terraform\s*\{'` - Detects terraform blocks

2. **Block Extraction** (`extract_blocks()`):
   - Finds all blocks of a given type in the file content
   - Extracts block name (for variable/output blocks)
   - Records line number for error reporting
   - Finds block boundaries using brace counting

3. **Sorting Verification** (`check_block_order()`):
   - Extracts block names from detected blocks
   - Creates sorted version using case-insensitive alphabetical sort
   - Compares current order with expected sorted order
   - Reports first out-of-order block with detailed context

4. **Error Reporting**:
   - Shows current order vs. expected order
   - Provides line numbers for out-of-order blocks
   - Suggests fixes using tfsort tool or manual reordering
   - Clear visual formatting with emojis (❌, 💡)

5. **File Focus**:
   - Primarily targets `variables.tf` and `outputs.tf` files
   - Uses regex to match these files: `(variables|outputs)\.tf$`
   - Can check any `.tf` file containing variable or output blocks

#### Tag Validation Checker

The tag validation checker validates resource tags/labels for compliance:

1. **Configuration Loading** (`_load_config()`):
   - Loads from YAML file (`.terraform-tags.yaml`) or JSON command-line arguments
   - Priority: command-line args > config file > defaults
   - Supports PyYAML for YAML parsing, fallback to JSON if PyYAML not available
   - Includes default comprehensive lists of taggable resources for AWS, Azure, GCP, Oracle Cloud

2. **Resource Detection** (`RESOURCE_BLOCK_PATTERN`):
   - Pattern: `r'^\s*resource\s+"([^"]+)"\s+"([^"]+)"\s*\{'`
   - Finds all resource blocks in `.tf` files
   - Extracts resource type and name
   - Checks if resource type is in taggable resources list

3. **Taggable Resource Identification** (`is_taggable_resource()`):
   - Maintains provider-specific lists of taggable resources
   - AWS: 100+ resources (uses `tags` attribute)
   - Azure: 40+ resources (uses `tags` attribute)
   - GCP: 30+ resources (uses `labels` attribute, not `tags`)
   - Oracle Cloud: 10+ resources
   - Can be extended/overridden in configuration

4. **Tag Extraction** (`extract_tags_from_resource()`):
   - Finds `tags = {}` or `labels = {}` blocks within resources
   - Parses static tag key-value pairs
   - Skips dynamic tags using `merge()`, `var.`, or `local.`
   - Returns dict of tags or None for dynamic tags

5. **Required Tag Validation** (`validate_required_tags()`):
   - Checks all required tags are present
   - Validates tag keys match exact case (case-sensitive)
   - Ensures tag values are non-empty
   - If `allowed_values` specified, validates values match exactly (case-sensitive)
   - If `pattern` specified, validates values against regex pattern
   - Reports helpful errors for case mismatches, missing tags, and pattern violations

6. **Optional Tag Validation** (`validate_optional_tags()`):
   - Only validates if optional tag is present
   - Checks tag key case sensitivity
   - Does not validate values (any value allowed)
   - Helps catch typos like "project" vs "Project"

7. **Provider-Specific Handling** (`get_tag_attribute_name()`):
   - AWS/Azure/Oracle: uses `tags`
   - GCP: uses `labels`
   - Automatically detects from resource type prefix

8. **Configuration Schema**:

   ```yaml
   required_tags:
     - name: "Environment"
       allowed_values: ["Development", "Staging", "Production"]  # Exact match
     - name: "Owner"
       pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"  # Email format
     - name: "CostCenter"
       pattern: "^CC-[0-9]{4}$"  # CC-#### format
   optional_tags:
     - name: "Project"
   taggable_resources:  # Optional: extend/override defaults
     aws: [...]
     azurerm: [...]
   ```

#### Template Sync Checker

The template sync checker validates repository scaffold files against a reference template:

1. **Initialization and Validation** (`__init__()`):
   - Validates that template path exists and is a directory
   - Resolves both template and repository paths to absolute paths
   - Initializes error and warning lists for tracking issues

2. **Exclusion Logic** (`should_exclude()`):
   - Excludes common VCS and build directories: `.git`, `__pycache__`, `.terraform`, `node_modules`
   - Excludes lock files and state files: `.terraform.lock.hcl`, `terraform.tfstate`
   - Excludes variable files containing sensitive data: `*.tfvars`
   - Supports both exact matches and pattern-based exclusions

3. **Hash Calculation** (`calculate_sha256()`):
   - Uses SHA256 hashing for file content comparison
   - Reads files in 4096-byte chunks for memory efficiency
   - Returns hexadecimal hash string for comparison
   - Handles both text and binary files

4. **Template Structure Extraction** (`get_template_structure()`):
   - Recursively walks template directory using `rglob("*")`
   - Builds set of directory paths and dict of file paths with hashes
   - Filters out excluded directories and their contents
   - Skips files inside excluded parent directories

5. **Directory Validation** (`check_directories()`):
   - Verifies all template directories exist in repository
   - Detects missing directories
   - Detects paths that should be directories but are files
   - Provides specific error messages with expected locations

6. **File Validation** (`check_files()`):
   - Checks each template file exists in repository
   - Compares file content using SHA256 hashes
   - Detects three types of errors:
     - Missing files (file exists in template but not in repo)
     - Content mismatches (file exists but content differs)
     - Type mismatches (path is directory instead of file)
   - Reports both repository and template SHA256 hashes for debugging

7. **Error Reporting** (`print_results()`):
   - Displays warnings (non-fatal issues like unreadable files)
   - Shows detailed error messages with file paths and hash values
   - Provides actionable remediation guidance
   - Uses emojis for visual clarity (📁 directories, 📄 files, ⚠️ warnings)

8. **Usage Pattern**:
   - Requires `--template-path` argument pointing to reference template
   - Optional `--repo-root` argument (defaults to current directory)
   - Manual stage hook for explicit invocation
   - Typical use: `pre-commit run check-template-sync --hook-stage manual`

## Common Development Commands

### Testing the hooks

```bash
# Test provider config checker on specific files
python check_provider_config.py test/test_azure_old.tf

# Test module version checker
python check_module_versions.py test/test_module_conflicts.tf

# Test module version checker excluding specific directories
python check_module_versions.py --exclude-dir test/ main.tf

# Test tfsort checker
python check_tfsort.py test/test_tfsort_sorted_variables.tf
python check_tfsort.py test/test_tfsort_unsorted.tf  # Should fail

# Test tag validation checker
python src/check_terraform_tags.py --config test/.terraform-tags-test.yaml test/test_tags_valid.tf  # Should pass
python src/check_terraform_tags.py --config test/.terraform-tags-test.yaml test/test_tags_invalid.tf  # Should fail

# Test tag validation with inline JSON args
python src/check_terraform_tags.py --required-tags '[{"name":"Environment","allowed_values":["Development","Staging","Production"]},{"name":"Owner"}]' test/test_tags_valid.tf

# Test template sync checker
python src/check_template_sync.py --template-path test/template_reference --repo-root test/template_test_repo  # Should pass
python src/check_template_sync.py --template-path test/template_reference --repo-root test/template_test_repo_mismatch  # Should fail

# Test multiple providers
python check_provider_config.py test/*.tf

# Run specific hook via pre-commit framework
pre-commit run check-provider-config --all-files
pre-commit run check-module-versions --all-files
pre-commit run check-tfsort --all-files
pre-commit run check-terraform-tags --all-files

# Run all pre-commit hooks
pre-commit run --all-files

# Run manual stage hooks (TOFU tests and template sync)
pre-commit run check-tofu-unit-tests --hook-stage manual
pre-commit run check-tofu-integration-tests --hook-stage manual
pre-commit run check-template-sync --hook-stage manual

# Run full multi-cloud verification
./verify_multi_cloud.sh
```

### Running automated tests

```bash
# Run the Python test suite (from root directory)
./run_tests.sh

# Or run directly from test directory
cd test && python test_hooks.py

# Run tests with pytest (if installed)
pytest test/

# Run tests with coverage report
pytest test/ --cov=. --cov-report=html --cov-report=term

# Generate coverage report in HTML format
pytest test/ --cov=. --cov-report=html
# View results in htmlcov/index.html
```

### Installation/Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Automated setup (requires git repo)
./setup.sh

# Manual setup
pip install pre-commit
pre-commit install
```

### Version Management

```bash
# Create a new version tag
./create_version_tag.sh 1.0.0

# Create version tag using GitVersion (if installed)
./create_version_tag.sh

# This script will:
# - Create a semantic version tag (e.g., v1.0.0)
# - Move the 'latest' tag to point to the new version
# - Push both tags to the remote repository
```

## File Structure

```text
.
├── src/
│   ├── check_provider_config.py         # Provider convention checker hook
│   ├── check_module_versions.py         # Module version conflict checker
│   ├── check_tfsort.py                  # TFSort compliance checker
│   ├── check_tofu_unit_tests.py         # Terraform/OpenTofu unit test runner
│   ├── check_tofu_integration_tests.py  # Terraform/OpenTofu integration test runner
│   ├── check_terraform_tags.py          # Terraform resource tag validation hook
│   └── check_template_sync.py           # Repository scaffold file synchronization checker
├── .pre-commit-config.yaml              # Pre-commit hooks configuration (local dev)
├── .pre-commit-hooks.yaml               # Remote hook definitions (for users)
├── .secrets.baseline                    # detect-secrets baseline file
├── GitVersion.yml                       # GitVersion configuration
├── pyproject.toml                       # Python project & tool configuration
├── requirements.txt                     # Python dependencies
├── setup.sh                             # Automated installer
├── verify_multi_cloud.sh                # Multi-provider verification
├── run_tests.sh                         # Convenience script to run tests from root
├── create_version_tag.sh                # Version tagging and release script
├── README.md                            # Primary documentation
├── CLAUDE.md                            # This file - technical architecture for AI assistants
├── docs/
│   ├── START_HERE.md                    # Quick start guide
│   ├── INDEX.md                         # Documentation index
│   ├── QUICK_REFERENCE.md               # Pattern comparison
│   └── MULTI_CLOUD_SUPPORT.md           # Multi-cloud examples
├── examples/
│   ├── example_multi_cloud_module.tf    # 4-provider module example
│   └── example_multi_cloud_root.tf      # Root module calling examples
└── test/
    ├── test_provider_config.py          # Unit tests for provider config checker
    ├── test_module_versions.py          # Unit tests for module version checker
    ├── test_tfsort.py                   # Unit tests for tfsort checker
    ├── test_tofu_unit_tests.py          # Unit tests for TOFU unit test runner
    ├── test_tofu_integration_tests.py   # Unit tests for TOFU integration test runner
    ├── test_check_terraform_tags_unit.py # Unit tests for tag validation checker
    ├── test_template_sync.py            # Unit tests for template sync checker
    ├── template_reference/              # Reference template for testing template sync
    │   ├── .editorconfig
    │   ├── .gitignore
    │   ├── Jenkinsfile
    │   ├── .terraform-tags.yaml
    │   └── .github/workflows/terraform.yml
    ├── template_test_repo/              # Test repo matching template (should pass)
    ├── template_test_repo_mismatch/     # Test repo with mismatches (should fail)
    ├── test_module_conflicts.tf         # Module version conflict test (should fail)
    ├── test_module_consistent.tf        # Consistent module versions (should pass)
    ├── test_tfsort_unsorted.tf          # Unsorted variables/outputs (should fail)
    ├── test_tfsort_sorted_variables.tf  # Properly sorted variables (should pass)
    ├── test_tfsort_sorted_outputs.tf    # Properly sorted outputs (should pass)
    ├── test_azure_old.tf                # Azure old-style test case
    └── [other test cases]               # AWS, GCP, Oracle examples
```

## Key Patterns

### Old Pattern (Detected and Blocked)

```hcl
provider "aws" {  # or azurerm, google, oci, any provider
  region = var.region
}
```

### New Pattern (Required)

```hcl
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.0"
      configuration_aliases = [aws.main]
    }
  }
}

# Resources reference: provider = aws.main
```

## Error Output Format

When violations are detected, the hook outputs:

1. Header with emoji icons (📁 File, 📍 Line, ⚠️ Warning)
2. Specific error message with provider name
3. Context-specific remediation guidance (different for modules vs roots)
4. Example fix patterns for common providers

## Testing Strategy

The repository includes test files demonstrating:

- Old-style patterns that should fail (test_*_old.tf)
- New-style patterns that should pass (example_*.tf)
- Multi-cloud scenarios with 4+ providers
- Module version conflicts and consistency checks
- TFSort compliance (sorted vs unsorted variables/outputs)
- test_hooks.py runs automated tests for all hooks expecting specific pass/fail outcomes

## Provider Support

**Explicitly tested**: AWS (aws), Azure (azurerm), GCP (google), Oracle Cloud (oci)

**Works with any provider** in the Terraform Registry - the detection is based on HCL syntax patterns, not provider-specific knowledge.

## Important Notes

- This is a **static analysis tool** - it parses .tf files, doesn't execute Terraform
- Python 3 required (uses argparse, re, pathlib, typing)
- **No external Python dependencies** for the checker itself - only uses standard library
- External dependencies for development (see [requirements.txt](requirements.txt)):
  - `pre-commit` - Hook framework
  - `pytest` - Testing framework (optional but recommended)
  - `pytest-cov` - Coverage reporting (optional but recommended)
- Designed to work with both Terraform and OpenTofu (same HCL syntax)
- Exit code 0 = pass, 1 = violations found (standard pre-commit convention)

## Development Guidelines

### Pre-commit Hook Configuration

The repository contains two pre-commit configuration files:

1. **[.pre-commit-config.yaml](.pre-commit-config.yaml)** - Local development configuration
2. **[.pre-commit-hooks.yaml](.pre-commit-hooks.yaml)** - Remote hook definitions for users

#### Local Development Configuration (.pre-commit-config.yaml)

The [.pre-commit-config.yaml](.pre-commit-config.yaml) file configures:

1. **Standard Python quality hooks**:
   - Code formatting and linting (ruff)
   - Type checking (mypy)
   - Common checks (trailing whitespace, large files, etc.)

2. **Security hooks**:
   - **bandit** - Finds common security issues in Python code
   - **safety** - Checks dependencies for known vulnerabilities
   - **pip-audit** - Audits Python packages for security issues
   - **detect-secrets** - Prevents committing secrets (API keys, passwords, tokens)
   - **vulture** - Finds unused/dead code

3. **Shell script quality**:
   - **shellcheck** - Lints bash/shell scripts (setup.sh, verify_multi_cloud.sh, run_tests.sh)

4. **Local hooks**:
   - `check-provider-config` - The main Terraform provider checker (runs on commit)
   - `pytest` - Run tests (runs on pre-push)
   - `pytest-coverage` - Run tests with coverage (manual stage)

5. **Dependency management**:
   - Pre-commit manages dependencies for remote hooks automatically
   - The `check-provider-config` hook needs NO additional dependencies (stdlib only)
   - pytest/coverage hooks use `language: system` and require local installation

6. **Configuration files**:
   - [pyproject.toml](pyproject.toml) - Contains configuration for bandit, ruff, mypy, pytest, and coverage
   - [.secrets.baseline](.secrets.baseline) - Baseline for detect-secrets (tracks known/approved patterns)
   - Settings are centralized for consistency across tools

#### Remote Hook Definitions (.pre-commit-hooks.yaml)

The [.pre-commit-hooks.yaml](.pre-commit-hooks.yaml) file defines hooks for remote usage:

- **Purpose**: Allows other projects to use these hooks via `repos:` in their `.pre-commit-config.yaml`
- **Contains**: Hook IDs, entry points, file patterns, and minimum pre-commit version requirements
- **Usage Pattern**: Users reference this repository and specify hook IDs (e.g., `check-provider-config`)
- **Important**: When adding new hooks or modifying existing ones, update BOTH configuration files

Example of how users consume these hooks:
```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v1.0.0
    hooks:
      - id: check-provider-config
      - id: check-module-versions
```

### When Modifying the Checker Logic

1. **Regex Pattern Changes**: If modifying `PROVIDER_BLOCK_PATTERN` or `REQUIRED_PROVIDERS_PATTERN`, test against all example files:
   - test/test_azure_old.tf (should fail)
   - examples/example_multi_cloud_module.tf (should pass)
   - Run `./verify_multi_cloud.sh` to verify all providers

2. **Context Window**: The 500-character lookback in [check_provider_config.py:107](check_provider_config.py#L107) is critical for filtering false positives. Changes to this may affect detection accuracy.

3. **Module Detection**: The `is_module_directory()` method at [check_provider_config.py:52-65](check_provider_config.py#L52-L65) uses heuristics. If changing these, ensure both root and module scenarios are tested.

### Common Provider Patterns

When adding examples or documentation:

- **AWS**: Uses `hashicorp/aws`, commonly needs region configuration
- **Azure (azurerm)**: Uses `hashicorp/azurerm`, requires `features {}` block (this is correct in both patterns)
- **GCP**: Uses `hashicorp/google` or `hashicorp/google-beta`
- **Oracle (oci)**: Uses `oracle/oci`, requires authentication config

### Error Message Philosophy

Error messages follow this structure (see [check_provider_config.py:121-134](check_provider_config.py#L121-L134)):

1. Clearly state what was detected (provider name)
2. Explain the consequence (blocks for_each/depends_on)
3. Provide specific remediation (different for modules vs roots)
4. Link to official Terraform documentation

### Windows Compatibility

This codebase is developed on Windows (as evidenced by the working directory):

- Python scripts work natively on Windows
- Bash scripts (setup.sh, verify_multi_cloud.sh) require WSL, Git Bash, or similar
- Path handling uses pathlib for cross-platform compatibility
- Use forward slashes in documentation examples

### CI/CD Integration Patterns

The hook can be integrated in multiple ways:

1. **Pre-commit framework** (recommended): `pre-commit run check-provider-config --all-files`
2. **Direct Python execution**: `python check_provider_config.py **/*.tf`
3. **With specific files**: Hook receives filenames via command-line args (see [check_provider_config.py:214](check_provider_config.py#L214))

### Documentation Structure

- **README.md**: Primary user-facing documentation, installation guide
- **docs/START_HERE.md**: Quick start for new users, package overview
- **docs/MULTI_CLOUD_SUPPORT.md**: Detailed multi-cloud patterns and examples
- **docs/QUICK_REFERENCE.md**: Side-by-side pattern comparison
- **CLAUDE.md**: This file - technical architecture for AI assistants

### Testing Approach

The test files serve dual purposes:

1. **Validation**: Verify the hook detects old patterns correctly
2. **Documentation**: Show real-world provider examples

When adding new provider examples:

- Create `test/test_<provider>_old.tf` for old pattern (should fail)
- Add corresponding example in `examples/` for new pattern (should pass)
- Update `verify_multi_cloud.sh` if adding a major cloud provider
