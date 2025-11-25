# Terraform/OpenTofu Provider Configuration Pre-Commit Hooks

**🌐 Works with ALL cloud providers: AWS, Azure, GCP, Oracle, and hundreds more!**

This repository provides pre-commit hooks for Terraform/OpenTofu projects:

1. **Provider Configuration Checker** - Detects old-style provider configurations that prevent `for_each` and `depends_on` at the module level
2. **Module Version Checker** - Ensures consistent module versions across all references
3. **TFSort Checker** - Verifies variables and outputs are alphabetically sorted per tfsort conventions
4. **Tag Validation Checker** - Validates resource tags for compliance with required tags, case sensitivity, and allowed values
5. **TOFU Unit Test Runner** - Ensures Terraform/OpenTofu unit tests pass before commits/pushes
6. **TOFU Integration Test Runner** - Runs integration tests for comprehensive validation

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
  - repo: https://github.com/TMAtwood/terraform-provider-convention-checker
    rev: v0.1.0  # Use a specific version tag or branch
    hooks:
      - id: check-provider-config
      - id: check-module-versions
      - id: check-tfsort
      - id: check-terraform-tags
        args: [--config, .terraform-tags.yaml]  # Optional: specify config file
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

- **Alphabetical sorting** - Ensures variables and outputs are in alphabetical order
- **Focused checking** - Primarily checks `variables.tf` and `outputs.tf` files
- **Clear error messages** - Shows current vs. expected order with line numbers
- **Easy fixes** - Provides commands to automatically fix sorting issues

#### Usage

```bash
# Check specific files
python check_tfsort.py variables.tf outputs.tf

# Via pre-commit (runs automatically on variables.tf and outputs.tf)
pre-commit run check-tfsort --all-files

# Install tfsort to automatically fix sorting
# See: https://github.com/AlexNabokikh/tfsort
```

#### Example Output

When sorting issues are detected:

```
❌ Variable blocks are not sorted alphabetically.
   Expected 'apple_config' but found 'zebra_config' at line 4.

   Current order: zebra_config, apple_config, monkey_config, banana_config
   Expected order: apple_config, banana_config, monkey_config, zebra_config

   💡 Fix: Run 'tfsort variables.tf' or manually reorder blocks alphabetically.
```

#### Integration with tfsort

This hook verifies compliance with tfsort standards. To automatically fix sorting issues, install [tfsort](https://github.com/AlexNabokikh/tfsort):

```bash
# Install tfsort (see GitHub releases for download links)
# https://github.com/AlexNabokikh/tfsort/releases

# Fix a single file
tfsort variables.tf

# Fix all .tf files recursively
tfsort -r .
```

### 4. Tag Validation Checker (`check-terraform-tags`)

#### Description

Validates that Terraform/OpenTofu resources have required tags with correct case sensitivity and allowed values. Works universally with AWS (tags), Azure (tags), GCP (labels), Oracle Cloud, and all other providers.

#### Features

- **Required Tags** - Enforce specific tags on all taggable resources
- **Case Sensitivity** - Validate exact case for tag keys (e.g., "Environment" not "environment")
- **Allowed Values** - Restrict tag values to a predefined list with case-sensitive validation
- **Optional Tags** - Validate case sensitivity for optional tags when present
- **Multi-Provider Support** - Built-in support for AWS, Azure, GCP, Oracle Cloud with 100+ taggable resources
- **Flexible Configuration** - Use YAML config file or JSON command-line arguments

#### Quick Start

Create a `.terraform-tags.yaml` configuration file:

```yaml
required_tags:
  - name: Environment
    allowed_values:
      - Development
      - Staging
      - Production
  - name: Owner
  - name: CostCenter

optional_tags:
  - name: Project
  - name: Description
```

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-provider-convention-checker
    rev: v1.0.0
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
# AWS resource with required tags
resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  tags = {
    Environment = "Production"  # Correct case, valid value
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
    Project     = "WebApp"  # Optional tag
  }
}

# GCP resource uses "labels" instead of "tags"
resource "google_compute_instance" "app" {
  name         = "app-server"
  machine_type = "n1-standard-1"

  labels = {
    Environment = "Development"
    Owner       = "gcp-team@example.com"
    CostCenter  = "CC-5678"
  }
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

# ❌ FAIL: Invalid tag value
resource "azurerm_resource_group" "main" {
  name     = "my-rg"
  location = "East US"
  tags = {
    Environment = "Testing"  # Not in allowed values
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
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

### 5. TOFU Unit Test Runner (`check-tofu-unit-tests`)

#### Description

Runs Terraform/OpenTofu unit tests (`terraform test` or `tofu test`) as part of your pre-commit workflow to ensure unit tests pass before code is pushed.

#### Unit Test Features

- **Auto-detection** - Automatically finds test directories (`tests/`, `test/`, or `*_test/`)
- **Custom test directory** - Specify a custom test directory with `--test-dir`
- **Flexible** - Works with both `terraform test` and `tofu test` commands (tries tofu first, then terraform)
- **Command selection** - Explicitly choose `tofu` or `terraform` with `--command`
- **Verbose mode** - Optional verbose output for debugging

#### Unit Test Usage

**In your `.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-provider-convention-checker
    rev: v1.0.0
    hooks:
      - id: check-tofu-unit-tests
        stages: [pre-push]  # Recommended: run on push, not every commit
```

**With custom test directory:**

```yaml
      - id: check-tofu-unit-tests
        stages: [pre-push]
        args: ['--test-dir=my-custom-tests']
```

**Force OpenTofu or Terraform:**

```yaml
      - id: check-tofu-unit-tests
        stages: [pre-push]
        args: ['--command=tofu']  # or '--command=terraform'
```

**Run manually:**

```bash
# Auto-detect test directory (tries tofu first, then terraform)
python check_tofu_unit_tests.py

# Specify custom directory
python check_tofu_unit_tests.py --test-dir=./my-tests

# Use OpenTofu specifically
python check_tofu_unit_tests.py --command=tofu

# Use Terraform specifically
python check_tofu_unit_tests.py --command=terraform

# Verbose output
python check_tofu_unit_tests.py --verbose
```

### 5. TOFU Integration Test Runner (`check-tofu-integration-tests`)

#### Overview

Runs Terraform/OpenTofu integration tests (`terraform test` or `tofu test`) as part of your pre-commit workflow to ensure integration tests pass before code is pushed.

#### Integration Test Features

- **Auto-detection** - Automatically finds integration test directories (`integration_tests/`, `integration/`, `tests/integration/`, or `test/integration/`)
- **Custom test directory** - Specify a custom integration test directory with `--test-dir`
- **Flexible** - Works with both `terraform test` and `tofu test` commands (tries tofu first, then terraform)
- **Command selection** - Explicitly choose `tofu` or `terraform` with `--command`
- **Verbose mode** - Optional verbose output for debugging

#### Integration Test Usage

**In your `.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-provider-convention-checker
    rev: v1.0.0
    hooks:
      - id: check-tofu-integration-tests
        stages: [pre-push]  # Recommended: run on push, not every commit
```

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

Copyright (c) 2025 Thomas M. Atwood

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
