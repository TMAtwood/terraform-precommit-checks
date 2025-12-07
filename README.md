# Terraform/OpenTofu Provider Configuration Pre-Commit Hooks

**🌐 Works with ALL cloud providers: AWS, Azure, GCP, Oracle, and hundreds more!**

This repository provides pre-commit hooks for Terraform/OpenTofu projects:

1. **Provider Configuration Checker** - Detects old-style provider configurations that prevent `for_each` and `depends_on` at the module level
2. **Module Version Checker** - Ensures consistent module versions across all references
3. **TFSort Checker** - Verifies variables and outputs are alphabetically sorted per tfsort conventions
4. **Tag Validation Checker** - Validates resource tags for compliance with required tags, case sensitivity, and allowed values
5. **Template Sync Checker** - Validates repository scaffold files match a reference template using SHA256 hash comparison
6. **TOFU Unit Test Runner** - Ensures Terraform/OpenTofu unit tests pass before commits/pushes
7. **TOFU Integration Test Runner** - Runs integration tests for comprehensive validation

**Provider-Agnostic:** These tools work universally with any Terraform provider - whether you're using AWS, Azure, Google Cloud, Oracle Cloud, VMware, Kubernetes, or any of the 3,000+ providers in the Terraform Registry.

## Hooks

### 1. Provider Configuration Checker (`check-provider-config`)

## Problem

When modules use the old provider initialization pattern:

```hcl
# Works with ANY provider - AWS, Azure, GCP, Oracle, etc.
provider "aws" {        # or "azurerm", "google", "oci", etc.
  region = var.region
}
```

It prevents you from using `for_each` and `depends_on` when calling the module:

```hcl
# ❌ This won't work with old-style provider config
module "example" {
  source   = "./modules/my-module"
  for_each = var.instances  # ERROR!
  depends_on = [aws_iam_role.example]  # ERROR!
}
```

## Solution

Use the new provider configuration pattern with `required_providers`:

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
```

Then pass providers when calling the module:

```hcl
# ✅ This works!
module "example" {
  source = "./modules/my-module"

  providers = {
    aws.main = aws.us-east-1
  }

  for_each   = var.instances  # Works!
  depends_on = [aws_iam_role.example]  # Works!
}
```

## Installation

### Prerequisites

```bash
pip install pre-commit
```

### Setup

#### Option 1: Remote Hook (Recommended)

Add this repository to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v0.1.0  # Use a specific version tag or branch
    hooks:
      - id: check-provider-config
      - id: check-module-versions
      - id: check-tfsort
      - id: check-terraform-tags
        args: [--config, .terraform-tags.yaml]  # Optional: specify config file
      # Optional: Template sync checker (manual stage)
      # - id: check-template-sync
      #   args: [--template-path, /path/to/your/template]
      #   stages: [manual]
      # Optional: Add test hooks (run on push, not every commit)
      # - id: check-tofu-unit-tests
      #   stages: [pre-push]
      # - id: check-tofu-integration-tests
      #   stages: [pre-push]
```

Then install the pre-commit hooks:

```bash
pre-commit install
# Optional: If using manual stage hooks (unit/integration tests)
pre-commit install --hook-type pre-push
```

#### Option 2: Local Hook

If you need to customize the checker script:

1. Copy `check_provider_config.py` to your repository root (or a `scripts/` directory)

2. Create or update `.pre-commit-config.yaml` in your repository root:

```yaml
repos:
  - repo: local
    hooks:
      - id: check-provider-config
        name: Check for old-style provider configurations
        entry: python check_provider_config.py
        language: python
        files: \.tf$
        pass_filenames: true
```

3. Install the pre-commit hook:

```bash
pre-commit install
```

## Usage

### Automatic (on commit)

Once installed, the hook runs automatically on every commit. If old-style provider configurations are detected, the commit will be blocked with a detailed error message.

### Manual

Run the hook on all files:

```bash
pre-commit run check-provider-config --all-files
```

Run directly on specific files:

```bash
python check_provider_config.py path/to/file.tf path/to/another.tf
```

## What It Detects

The hook detects:

1. **Direct provider blocks** in modules (outside of `required_providers`)
2. **Missing `required_providers` declarations** for providers being used
3. **Old patterns** that prevent module-level meta-arguments

The hook is smart enough to:

- ✅ Skip provider configurations inside `required_providers` blocks
- ✅ Skip `configuration_aliases` declarations (which are correct)
- ✅ Skip mock providers used in testing
- ✅ Distinguish between root modules and reusable modules

## Error Output

When an old-style configuration is detected, you'll see:

```text
================================================================================
❌ OLD-STYLE PROVIDER CONFIGURATION DETECTED
================================================================================

📁 File: modules/example/main.tf
📍 Line: 15
⚠️  Old-style provider configuration detected for 'aws'. This prevents module-level for_each and depends_on.
  → Modules should use required_providers with configuration_aliases instead.
  → See: https://developer.hashicorp.com/terraform/language/modules/develop/providers
```

## Migration Guide

### For Reusable Modules

**Before (Old Pattern):**

```hcl
# modules/my-module/main.tf
provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "example" {
  bucket = var.bucket_name
}
```

**After (New Pattern):**

```hcl
# modules/my-module/main.tf
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.0"
      configuration_aliases = [aws.main]
    }
  }
}

resource "aws_s3_bucket" "example" {
  provider = aws.main
  bucket   = var.bucket_name
}
```

**Module Usage:**

```hcl
# Root module
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

module "buckets" {
  source   = "./modules/my-module"
  for_each = var.environments

  providers = {
    aws.main = aws.us_east_1
  }

  bucket_name = each.value.bucket_name
}
```

### For Root Modules

**Before:**

```hcl
provider "aws" {
  region = "us-east-1"
}
```

**After:**

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
```

## Benefits

✅ **Enable `for_each` on modules** - Create multiple instances of modules dynamically

✅ **Enable `depends_on` on modules** - Control module dependency ordering

✅ **Better provider management** - Explicit version constraints and source declarations

✅ **Improved reusability** - Modules can work with any provider configuration

✅ **Prevent runtime errors** - Catch configuration issues before deployment

✅ **Universal compatibility** - Works with ALL Terraform providers (AWS, Azure, GCP, Oracle, Kubernetes, and 3,000+ more)

### 2. Module Version Checker (`check-module-versions`)

#### Description

Detects conflicting module versions or git refs in Terraform/OpenTofu configurations. Ensures all references to the same module use consistent versions, preventing subtle bugs and maintenance issues.

#### Features

- **Version consistency** - Detects when the same module is referenced with different versions
- **Git ref tracking** - Supports git modules with refs, tags, and commit hashes
- **Registry modules** - Works with Terraform Registry modules (e.g., `terraform-aws-modules/vpc/aws`)
- **Detailed reports** - Shows all conflicts with file locations and line numbers
- **Skip local modules** - Ignores local path modules (e.g., `./modules/...`)

#### Usage

```bash
# Check specific files
python check_module_versions.py main.tf modules.tf

# Via pre-commit (runs automatically on .tf files)
pre-commit run check-module-versions --all-files
```

#### Example Output

```
❌ Found conflicting versions for module: terraform-aws-modules/vpc/aws

  File: environments/dev/main.tf:10
  Version: 3.0.0

  File: environments/prod/main.tf:15
  Version: 3.1.0

💡 Fix: Update all references to use the same version
```

### 3. TFSort Checker (`check-tfsort`)

#### Description

Verifies that variable and output blocks in Terraform files are sorted alphabetically according to [tfsort](https://github.com/AlexNabokikh/tfsort) conventions. This promotes consistency and makes it easier to find and maintain variables and outputs.

#### Features

- **Comprehensive validation** - Uses the actual `tfsort` binary for complete checking (when installed)
- **Alphabetical sorting** - Ensures variables and outputs are in alphabetical order
- **Spacing & formatting** - Detects incorrect spacing and unnecessary leading/trailing newlines
- **Focused checking** - Primarily checks `variables.tf` and `outputs.tf` files
- **Clear error messages** - Shows a diff of what tfsort would change
- **Graceful fallback** - Falls back to built-in block order checking if tfsort is not installed

#### How It Works

The checker operates in two modes:

1. **With tfsort binary (recommended)**: When `tfsort` is installed and available in PATH, the hook runs `tfsort --dry-run` and compares the output to the original file. This catches **all** issues that tfsort would fix, including:
   - Block ordering (variables, outputs, locals, terraform)
   - Spacing between blocks
   - Leading/trailing newlines
   - Any other formatting tfsort normalizes

2. **Without tfsort binary (fallback)**: When `tfsort` is not installed, the hook uses built-in checking that only verifies block alphabetical order. This is less comprehensive but still catches major sorting issues.

#### Usage

```bash
# Check specific files
python src/check_tfsort.py variables.tf outputs.tf

# Via pre-commit (runs automatically on variables.tf and outputs.tf)
pre-commit run check-tfsort --all-files

# Disable tfsort binary usage (use built-in checking only)
python src/check_tfsort.py --no-tfsort-binary variables.tf
```

#### Example Output

When tfsort binary is available and sorting issues are detected:

```text
🔍 TFSort Compliance Check Failed
   (Using tfsort binary for comprehensive checking)

📁 File: variables.tf
📍 Line: 1
❌ File is not properly sorted per tfsort conventions.

   The following changes would be made by tfsort:

   --- variables.tf (current)
   +++ variables.tf (after tfsort)
   @@ -1,2 +1,2 @@
   -variable "zebra" {}
   +variable "apple" {}
   +variable "zebra" {}
   -variable "apple" {}

   💡 Fix: Run 'tfsort variables.tf' to automatically sort the file.
```

When using built-in fallback (tfsort not installed):

```text
🔍 TFSort Compliance Check Failed
   (Using built-in block order checking (tfsort not found))

❌ Variable blocks are not sorted alphabetically.
   Expected 'apple' but found 'zebra' at line 1.

   Current order: zebra, apple
   Expected order: apple, zebra

   💡 Fix: Run 'tfsort variables.tf' or manually reorder blocks alphabetically.
```

#### Integration with tfsort

For comprehensive validation, install [tfsort](https://github.com/AlexNabokikh/tfsort):

```bash
# Install tfsort (see GitHub releases for download links)
# https://github.com/AlexNabokikh/tfsort/releases

# Verify installation
tfsort --version

# Fix a single file
tfsort variables.tf

# Fix all .tf files recursively
tfsort -r .
```

**Why install tfsort?**

- The hook will automatically detect and use tfsort for more comprehensive validation
- Catches spacing and formatting issues, not just block order
- Provides a diff showing exactly what would change
- tfsort can automatically fix all detected issues

### 4. Tag Validation Checker (`check-terraform-tags`)

#### Description

Validates that Terraform/OpenTofu resources have required tags with correct case sensitivity and allowed values. Works universally with AWS (tags), Azure (tags), GCP (labels), Oracle Cloud, and all other providers.

#### Features

- **Required Tags** - Enforce specific tags on all taggable resources
- **Case Sensitivity** - Validate exact case for tag keys (e.g., "Environment" not "environment")
- **Allowed Values** - Restrict tag values to a predefined list with case-sensitive validation
- **Pattern Validation** - Use regex patterns to enforce tag value formats (e.g., email, cost center, ticket ID)
- **Optional Tags** - Validate case sensitivity for optional tags when present
- **Multi-Provider Support** - Built-in support for AWS, Azure, GCP, Oracle Cloud with 100+ taggable resources
- **Flexible Configuration** - Use YAML config file or JSON command-line arguments

#### Quick Start

Create a `.terraform-tags.yaml` configuration file:

```yaml
required_tags:
  # Exact match validation with allowed values
  - name: Environment
    allowed_values:
      - Development
      - Staging
      - Production

  # Pattern validation for email format
  - name: Owner
    pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

  # Pattern validation for cost center format (CC-####)
  - name: CostCenter
    pattern: "^CC-[0-9]{4}$"

  # Pattern validation for ticket ID format (PROJECT-###)
  - name: TicketID
    pattern: "^[A-Z]+-[0-9]+$"

optional_tags:
  - name: Project
  - name: Description
```

**Common pattern examples:**

- **Email**: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$`
- **Cost Center** (CC-####): `^CC-[0-9]{4}$`
- **Ticket ID** (PROJ-###): `^[A-Z]+-[0-9]+$`
- **Date** (YYYY-MM-DD): `^[0-9]{4}-[0-9]{2}-[0-9]{2}$`
- **Version** (v#.#.#): `^v[0-9]+\\.[0-9]+\\.[0-9]+$`

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v0.1.0
    hooks:
      - id: check-terraform-tags
        args: [--config, .terraform-tags.yaml]
```

Or use inline JSON arguments:

```yaml
- id: check-terraform-tags
  args:
    - --required-tags
    - '[{"name":"Environment","allowed_values":["Dev","Staging","Prod"]},{"name":"Owner"}]'
    - --optional-tags
    - '[{"name":"Project"}]'
```

#### What It Validates

✅ **Checks performed:**

- All required tags are present on taggable resources
- Tag keys match exact case (case-sensitive)
- Tag values are non-empty
- Tag values match allowed list (if specified, case-sensitive)
- Optional tags use correct case (if present)

⏭️ **Skips validation for:**

- Non-taggable resources (based on comprehensive built-in lists)
- Dynamic tags using `merge()`, `var.`, or `local.`
- Test files (configurable with `exclude:`)

#### Example Valid Tags

```hcl
# ✅ PASS - AWS resource with required tags (allowed values + patterns)
resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  tags = {
    Environment = "Production"           # Matches allowed value
    Owner       = "team@example.com"     # Matches email pattern
    CostCenter  = "CC-1234"              # Matches CC-#### pattern
    TicketID    = "JIRA-5678"            # Matches PROJECT-### pattern
    Project     = "WebApp"               # Optional tag
  }
}

# ✅ PASS - GCP resource uses "labels" instead of "tags"
resource "google_compute_instance" "app" {
  name         = "app-server"
  machine_type = "n1-standard-1"

  labels = {
    Environment = "Development"          # Matches allowed value
    Owner       = "gcp-team@example.com" # Matches email pattern
    CostCenter  = "CC-5678"              # Matches CC-#### pattern
    TicketID    = "INFRA-100"            # Matches PROJECT-### pattern
  }
}
```

#### Pattern Validation Examples

```hcl
# ✅ PASS - Valid email pattern
tags = {
  Owner = "admin@example.com"
}

# ❌ FAIL - Invalid email (missing @ symbol)
tags = {
  Owner = "admin.example.com"  # Error: does not match pattern
}

# ✅ PASS - Valid cost center pattern
tags = {
  CostCenter = "CC-1234"
}

# ❌ FAIL - Invalid cost center (missing CC- prefix)
tags = {
  CostCenter = "1234"  # Error: does not match pattern ^CC-[0-9]{4}$
}

# ✅ PASS - Valid ticket ID pattern
tags = {
  TicketID = "JIRA-5678"
}

# ❌ FAIL - Invalid ticket ID (lowercase letters)
tags = {
  TicketID = "jira-5678"  # Error: does not match pattern ^[A-Z]+-[0-9]+$
}
```

#### Common Validation Errors

```hcl
# ❌ FAIL: Missing required tag
resource "aws_s3_bucket" "data" {
  bucket = "my-bucket"
  tags = {
    Environment = "Production"
    Owner       = "team@example.com"
    # Missing: CostCenter
  }
}

# ❌ FAIL: Wrong case for tag key
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    environment = "Production"  # Should be "Environment"
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
  }
}

# ❌ FAIL: Invalid allowed value
resource "azurerm_resource_group" "main" {
  name     = "my-rg"
  location = "East US"
  tags = {
    Environment = "Testing"  # Not in allowed values [Development, Staging, Production]
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
  }
}

# ❌ FAIL: Invalid pattern (email format)
resource "aws_instance" "app" {
  ami           = "ami-12345"
  instance_type = "t2.micro"
  tags = {
    Environment = "Production"
    Owner       = "admin"  # Does not match email pattern
    CostCenter  = "CC-1234"
  }
}

# ❌ FAIL: Invalid pattern (cost center format)
resource "aws_ebs_volume" "data" {
  availability_zone = "us-east-1a"
  size              = 10
  tags = {
    Environment = "Production"
    Owner       = "admin@example.com"
    CostCenter  = "1234"  # Missing CC- prefix, does not match ^CC-[0-9]{4}$
  }
}
```

#### Documentation

See [docs/TAG_VALIDATION.md](docs/TAG_VALIDATION.md) for:

- Complete configuration reference
- Advanced usage examples
- Provider-specific notes
- CI/CD integration
- Troubleshooting guide

### 5. Template Sync Checker (`check-template-sync`)

#### Description

Validates that repository scaffold files (like `.editorconfig`, `.gitignore`, `.pre-commit-config.yaml`, `Jenkinsfile`, `.terraform-tags.yaml`, etc.) match a reference template directory using SHA256 hash comparison. This ensures consistency and standardization across multiple OpenTofu/Terraform module repositories.

#### Features

- **SHA256 Hash Comparison** - Detects even single-character differences between files
- **Directory Structure Validation** - Ensures all required directories exist
- **Missing File Detection** - Identifies scaffold files that should be present
- **Content Mismatch Reporting** - Shows exact hash differences for debugging
- **Smart Exclusions** - Automatically skips `.git`, `__pycache__`, `.terraform`, `node_modules`, etc.
- **Verbose Error Messages** - Provides detailed information about each discrepancy
- **Manual Stage Hook** - Runs on-demand rather than every commit

#### Use Case

Perfect for organizations maintaining multiple Terraform module repositories where you want to ensure:

- All modules use the same `.editorconfig` settings
- All modules have consistent CI/CD pipeline definitions (`Jenkinsfile`, GitHub Actions)
- All modules follow the same tag validation rules (`.terraform-tags.yaml`)
- All modules use the same pre-commit configuration (`.pre-commit-config.yaml`)

#### Usage

1. Create a reference template directory with your standard scaffold files:

```bash
# Example template structure
template/
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml
├── .terraform-tags.yaml
├── Jenkinsfile
└── .github/
    └── workflows/
        └── terraform.yml
```

2. Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v0.1.0
    hooks:
      - id: check-template-sync
        args: [--template-path, /path/to/your/template]
        stages: [manual]  # Run manually, not on every commit
```

3. Run the checker:

```bash
# Run manually when you want to check template sync
pre-commit run check-template-sync --hook-stage manual

# Or run directly with Python
python src/check_template_sync.py --template-path /path/to/template
```

#### Example Output

**When repository matches template:**

```
✅ Repository structure matches template perfectly!
```

**When discrepancies are found:**

```
================================================================================
❌ TEMPLATE SYNC ERRORS DETECTED
================================================================================

The repository does not match the template structure.
Template path: /path/to/template
Repository path: /current/repo

Found 2 error(s):

📄 File content mismatch: .editorconfig
   Repository file: /current/repo/.editorconfig
   Template file:   /path/to/template/.editorconfig
   Repository SHA256: d40a86ccab9553003e0c477f2313c4539ee1182852f2597775ce2c3dd78ff7f3
   Template SHA256:   2a7e7dab35d8a34bddf8fa5fd0ae7b46759b9c82962abc0e88925734ffce2138
   → The file exists but has different content than the template.
   → Update this file to match the template version.
   → This ensures consistency and includes the latest best practices.
--------------------------------------------------------------------------------
📄 Missing file: Jenkinsfile
   Expected location: /current/repo/Jenkinsfile
   Template location: /path/to/template/Jenkinsfile
   → This file exists in the template but not in the repository.
   → Copy this file from the template to maintain consistency.
--------------------------------------------------------------------------------

================================================================================
💡 HOW TO FIX:
================================================================================

1. Review each error above to understand what's missing or different
2. For missing directories: Create them to match the template structure
3. For missing files: Copy them from the template directory
4. For mismatched files: Update them to match the template version
5. Re-run the hook to verify all issues are resolved

The template ensures your repository follows the latest best practices
and includes all necessary support files for OpenTofu modules.

================================================================================
```

#### Advanced Usage

**Specify custom repository root:**

```bash
python src/check_template_sync.py \
  --template-path ~/org/templates/terraform-module \
  --repo-root /path/to/specific/repo
```

**Use in CI/CD:**

```yaml
# GitHub Actions example
- name: Validate scaffold files
  run: |
    python src/check_template_sync.py \
      --template-path ${{ github.workspace }}/templates/terraform-module
```

**Exclude specific directories:**

The checker automatically excludes:

- Version control: `.git`
- Build artifacts: `__pycache__`, `.pytest_cache`, `.terraform`
- Dependencies: `node_modules`, `venv`
- State files: `.terraform.lock.hcl`, `terraform.tfstate`
- Variable files: `*.tfvars` (may contain sensitive data)

#### Best Practices

1. **Version Control Your Template** - Store your reference template in a separate Git repository
2. **Automate Template Updates** - Use CI/CD to automatically update modules when template changes
3. **Run Periodically** - Schedule template sync checks weekly/monthly to catch drift
4. **Document Template Changes** - Maintain a CHANGELOG for template updates
5. **Test Template Changes** - Test template modifications in a development module first

### 6. TOFU Unit Test Runner (`check-tofu-unit-tests`)

#### Overview

Runs Terraform/OpenTofu unit tests (`terraform test` or `tofu test`) as part of your pre-commit workflow to ensure unit tests pass before code is pushed.

#### Unit Test Features

- **Auto-detection** - Automatically finds test directories in standard and nested locations
- **Nested test support** - Handles tests in subdirectories like `test/fixture/unit_tests/` with automatic `-test-directory` flag
- **Custom test directory** - Specify a custom test directory with `--test-dir`
- **Flexible** - Works with both `terraform test` and `tofu test` commands (tries tofu first, then terraform)
- **Command selection** - Explicitly choose `tofu` or `terraform` with `--command`
- **Verbose mode** - Optional verbose output for debugging

#### Test Directory Auto-Detection

The hook searches for unit test directories in this priority order:

1. `test/fixture/unit_tests/` ← **Nested fixture structure**
2. `test/fixture/unit/` ← **Nested fixture structure**
3. `test/unit/` ← **Nested under test**
4. `tests/unit/`
5. `test/`
6. `tests/`
7. Any directory ending with `_test`

When tests are found in subdirectories (e.g., `test/fixture/unit_tests/`), the hook automatically detects the structure and applies the `-test-directory` flag, allowing it to work from your project root without manual directory changes.

#### Unit Test Directory Structures

**Standard flat structure** (works automatically):
```
project-root/
├── test/
│   ├── main.tf
│   └── main.tftest.hcl
```

**Nested fixture structure** (works automatically with auto-detection):
```
project-root/
├── test/
│   └── fixture/
│       └── unit_tests/
│           ├── main.tf
│           └── main.tftest.hcl
```

**How auto-detection works:**

When the hook finds tests at `test/fixture/unit_tests/`, it:

1. Changes to directory `test/fixture/`
2. Runs: `tofu test -test-directory unit_tests`
3. All relative paths resolve correctly
4. **No manual `cd` commands needed!**

#### Unit Test Usage

**In your `.pre-commit-config.yaml` (basic - uses auto-detection):**

```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v0.1.0
    hooks:
      - id: check-tofu-unit-tests
        stages: [pre-push]  # Recommended: run on push, not every commit
```

This works automatically for:

- ✅ Standard structures: `test/`, `tests/`, `test/unit/`, etc.
- ✅ Nested fixtures: `test/fixture/unit_tests/`, `test/fixture/unit/`
- ✅ No configuration needed!

**With explicit test directory:**

```yaml
      - id: check-tofu-unit-tests
        stages: [pre-push]
        args: ['--test-dir=test/fixture']  # Points to parent directory
```

**Force OpenTofu or Terraform:**

```yaml
      - id: check-tofu-unit-tests
        stages: [pre-push]
        args: ['--command=tofu']  # or '--command=terraform'
```

**Combine multiple arguments:**

```yaml
      - id: check-tofu-unit-tests
        stages: [pre-push]
        args:
          - '--test-dir=test/fixture'
          - '--command=tofu'
          - '--verbose'
```

**Run manually:**

```bash
# Auto-detect test directory (tries tofu first, then terraform)
python check_tofu_unit_tests.py

# Specify custom directory
python check_tofu_unit_tests.py --test-dir=./test/fixture

# Use OpenTofu specifically
python check_tofu_unit_tests.py --command=tofu

# Use Terraform specifically
python check_tofu_unit_tests.py --command=terraform

# Verbose output
python check_tofu_unit_tests.py --verbose

# Combine arguments
python check_tofu_unit_tests.py --test-dir=test/fixture --command=tofu --verbose
```

#### Real-World Example: Nested Fixture Structure

If your project has tests in `test/fixture/unit_tests/`:

```
my-terraform-project/
├── .pre-commit-config.yaml
├── main.tf
├── test/
│   └── fixture/
│       └── unit_tests/
│           ├── main.tf
│           └── main.tftest.hcl
```

**Just use the basic configuration:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v0.1.0
    hooks:
      - id: check-tofu-unit-tests
        stages: [pre-push]
```

The hook will:

1. ✅ Find `test/fixture/unit_tests/` automatically
2. ✅ Detect that tests are in a subdirectory
3. ✅ Change to `test/fixture/`
4. ✅ Run `tofu test -test-directory unit_tests`
5. ✅ Return control to project root
6. ✅ All done - no manual steps needed!

### 7. TOFU Integration Test Runner (`check-tofu-integration-tests`)

#### Overview

Runs Terraform/OpenTofu integration tests (`terraform test` or `tofu test`) as part of your pre-commit workflow to ensure integration tests pass before code is pushed.

#### Integration Test Features

- **Auto-detection** - Automatically finds integration test directories in standard and nested locations
- **Nested test support** - Handles tests in subdirectories like `test/fixture/integration_tests/` with automatic `-test-directory` flag
- **Custom test directory** - Specify a custom integration test directory with `--test-dir`
- **Flexible** - Works with both `terraform test` and `tofu test` commands (tries tofu first, then terraform)
- **Command selection** - Explicitly choose `tofu` or `terraform` with `--command`
- **Verbose mode** - Optional verbose output for debugging

#### Integration Test Directory Discovery

The hook searches for integration test directories in this priority order:

1. `test/fixture/integration_tests/` ← **Nested fixture structure**
2. `test/fixture/integration/` ← **Nested fixture structure**
3. `test/integration/` ← **Nested under test**
4. `tests/integration/`
5. `integration_tests/`
6. `integration/`
7. Any directory with "integration" in the name

When tests are found in subdirectories (e.g., `test/fixture/integration_tests/`), the hook automatically detects the structure and applies the `-test-directory` flag, allowing it to work from your project root without manual directory changes.

#### Integration Test Directory Structures

**Standard flat structure** (works automatically):

```tree
project-root/
├── integration/
│   ├── main.tf
│   └── main.tftest.hcl
```

**Nested fixture structure** (works automatically with auto-detection):

```tree
project-root/
├── test/
│   └── fixture/
│       └── integration_tests/
│           ├── main.tf
│           └── main.tftest.hcl
```

**How auto-detection works:**

When the hook finds tests at `test/fixture/integration_tests/`, it:

1. Changes to directory `test/fixture/`
2. Runs: `tofu test -test-directory integration_tests`
3. All relative paths resolve correctly
4. **No manual `cd` commands needed!**

#### Integration Test Usage

**In your `.pre-commit-config.yaml` (basic - uses auto-detection):**

```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v0.1.0
    hooks:
      - id: check-tofu-integration-tests
        stages: [pre-push]  # Recommended: run on push, not every commit
```

This works automatically for:

- ✅ Standard structures: `integration/`, `integration_tests/`, `test/integration/`, etc.
- ✅ Nested fixtures: `test/fixture/integration_tests/`, `test/fixture/integration/`
- ✅ No configuration needed!

**With explicit test directory:**

```yaml
      - id: check-tofu-integration-tests
        stages: [pre-push]
        args: ['--test-dir=test/fixture']  # Points to parent directory
```

**Force OpenTofu or Terraform:**

```yaml
      - id: check-tofu-integration-tests
        stages: [pre-push]
        args: ['--command=tofu']  # or '--command=terraform'
```

**Combine multiple arguments:**

```yaml
      - id: check-tofu-integration-tests
        stages: [pre-push]
        args:
          - '--test-dir=test/fixture'
          - '--command=tofu'
          - '--verbose'
```

**Run manually:**

```bash
# Auto-detect integration test directory (tries tofu first, then terraform)
python check_tofu_integration_tests.py

# Specify custom directory
python check_tofu_integration_tests.py --test-dir=./test/fixture

# Use OpenTofu specifically
python check_tofu_integration_tests.py --command=tofu

# Use Terraform specifically
python check_tofu_integration_tests.py --command=terraform

# Verbose output
python check_tofu_integration_tests.py --verbose

# Combine arguments
python check_tofu_integration_tests.py --test-dir=test/fixture --command=tofu --verbose
```

#### Integration Test Real-World Example: Nested Fixture Structure

If your project has tests in `test/fixture/integration_tests/`:

```tree
my-terraform-project/
├── .pre-commit-config.yaml
├── main.tf
├── test/
│   └── fixture/
│       └── integration_tests/
│           ├── main.tf
│           └── main.tftest.hcl
```

**Just use the basic configuration:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v0.1.0
    hooks:
      - id: check-tofu-integration-tests
        stages: [pre-push]
```

The hook will:

1. ✅ Find `test/fixture/integration_tests/` automatically
2. ✅ Detect that tests are in a subdirectory
3. ✅ Change to `test/fixture/`
4. ✅ Run `tofu test -test-directory integration_tests`
5. ✅ Return control to project root
6. ✅ All done - no manual steps needed!

**With custom test directory:**

```yaml
      - id: check-tofu-integration-tests
        stages: [pre-push]
        args: ['--test-dir=integration']
```

**Force OpenTofu or Terraform:**

```yaml
      - id: check-tofu-integration-tests
        stages: [pre-push]
        args: ['--command=tofu']  # or '--command=terraform'
```

**Run manually:**

```bash
# Auto-detect integration test directory (tries tofu first, then terraform)
python check_tofu_integration_tests.py

# Specify custom directory
python check_tofu_integration_tests.py --test-dir=./integration

# Use OpenTofu specifically
python check_tofu_integration_tests.py --command=tofu

# Use Terraform specifically
python check_tofu_integration_tests.py --command=terraform

# Verbose output
python check_tofu_integration_tests.py --verbose
```

## Multi-Cloud Support

This hook is completely **provider-agnostic** and works with:

- ✅ **AWS** (aws)
- ✅ **Azure** (azurerm)
- ✅ **Google Cloud** (google, google-beta)
- ✅ **Oracle Cloud** (oci)
- ✅ **Alibaba Cloud** (alicloud)
- ✅ **IBM Cloud** (ibm)
- ✅ **VMware vSphere** (vsphere)
- ✅ **Kubernetes** (kubernetes)
- ✅ **Any provider** in the [Terraform Registry](https://registry.terraform.io/browse/providers)

See [MULTI_CLOUD_SUPPORT.md](MULTI_CLOUD_SUPPORT.md) for detailed multi-cloud examples and patterns.

## Bypassing the Hook (Not Recommended)

If you need to commit without running hooks (not recommended for this check):

```bash
git commit --no-verify
```

## Integration with CI/CD

Add to your CI pipeline:

```bash
# In your CI script
pip install pre-commit
pre-commit run check-provider-config --all-files
```

Or run directly:

```bash
python check_provider_config.py **/*.tf
```

## Support for OpenTofu

This hook works with both Terraform and OpenTofu since they share the same HCL syntax for provider configuration.

## References

- [Terraform Module Providers Documentation](https://developer.hashicorp.com/terraform/language/modules/develop/providers)
- [Terraform Meta-Arguments](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)
- [OpenTofu Documentation](https://opentofu.org/docs/)

## License

MIT License

&copy; 2025, Thomas M. Atwood, CFA

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
