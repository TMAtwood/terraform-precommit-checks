# START HERE - Terraform/OpenTofu Pre-Commit Hooks

## What You Have

This repository provides **7 comprehensive pre-commit hooks** for Terraform/OpenTofu that work with **any cloud provider**:

| Hook | Purpose | Stage |
|------|---------|-------|
| **check-provider-config** | Enforces modern provider patterns | Automatic |
| **check-module-versions** | Ensures version consistency | Automatic |
| **check-tfsort** | Validates alphabetical sorting | Automatic |
| **check-terraform-tags** | Enforces tagging standards | Automatic |
| **check-template-sync** | Validates scaffold file consistency | Manual |
| **check-tofu-unit-tests** | Runs unit tests | Manual |
| **check-tofu-integration-tests** | Runs integration tests | Manual |

## Quick Start (5 Minutes)

### Step 1: Add to Your Repository

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v1.0.0  # Use the latest version
    hooks:
      # Automatic hooks (run on commit)
      - id: check-provider-config
      - id: check-module-versions
      - id: check-tfsort
      - id: check-terraform-tags
        args: [--config, .terraform-tags.yaml]

      # Manual hooks (run separately)
      # - id: check-template-sync
      #   args: [--template-path, /path/to/your/template]
      # - id: check-tofu-unit-tests
      # - id: check-tofu-integration-tests
```

### Step 2: Install Hooks

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the hooks
pre-commit install
```

### Step 3: Test the Hooks

```bash
# Run all automatic hooks
pre-commit run --all-files

# Run specific hooks
pre-commit run check-provider-config --all-files
pre-commit run check-terraform-tags --all-files

# Run manual test hooks
pre-commit run check-template-sync --hook-stage manual
pre-commit run check-tofu-unit-tests --hook-stage manual
```

## What Each Hook Does

### 1. Provider Configuration Checker

**Prevents:** Old-style `provider "name" { }` blocks that break `for_each` and `depends_on`

**Example issue detected:**

```hcl
# ❌ FAILS - Old pattern
provider "aws" {
  region = var.region
}
```

**Fix:**

```hcl
# ✅ PASSES - New pattern
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

**Learn more:** [PROVIDER_CONFIG_PATTERNS.md](PROVIDER_CONFIG_PATTERNS.md)

### 2. Module Version Checker

**Prevents:** Conflicting module versions across your codebase

**Example issue detected:**

```hcl
# ❌ FAILS - Conflicting versions
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"  # One file uses 3.0.0
}

# In another file...
module "vpc_prod" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.1.0"  # Another uses 3.1.0 - CONFLICT!
}
```

**Why it matters:** Prevents drift, ensures reproducible deployments

### 3. TFSort Checker

**Validates:** Variables and outputs are sorted alphabetically

**Example issue detected:**

```hcl
# ❌ FAILS - Wrong order
variable "region" {}
variable "environment" {}  # Should come before "region"
```

**Fix:**

```hcl
# ✅ PASSES - Alphabetical order
variable "environment" {}
variable "region" {}
```

**Why it matters:** Reduces merge conflicts, improves readability

### 4. Tag Validation

**Enforces:** Resource tagging standards with case sensitivity and value validation

**Example issue detected:**

```hcl
# ❌ FAILS - Missing required tags, wrong case
resource "aws_instance" "web" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    environment = "Production"  # Wrong case (should be "Environment")
    # Missing: Owner, CostCenter
  }
}
```

**Fix:**

```hcl
# ✅ PASSES - All required tags with correct case
resource "aws_instance" "web" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Environment = "Production"        # Correct case
    Owner       = "team@example.com"  # Required tag
    CostCenter  = "CC-1234"           # Required tag
  }
}
```

**Configuration:** Create `.terraform-tags.yaml`:

```yaml
required_tags:
  - name: Environment
    allowed_values:
      - Development
      - Staging
      - Production

  - name: Owner
    pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

  - name: CostCenter
    pattern: "^CC-[0-9]{4}$"

optional_tags:
  - name: Project
  - name: Description
```

**Learn more:** [TAG_VALIDATION.md](TAG_VALIDATION.md)

### 5. Template Sync Checker

**Validates:** Repository scaffold files match a reference template

**Why it matters:** Ensures all your Terraform modules use the same support files:

- `.editorconfig` - Same editor settings
- `.gitignore` - Same ignore patterns
- `.pre-commit-config.yaml` - Same CI/CD pipeline
- `Jenkinsfile` - Consistent automation
- `.terraform-tags.yaml` - Unified tagging rules

**Example issue detected:**

```text
❌ FAILS - File content mismatch: .editorconfig
   Repository SHA256: d40a86ccab9553003e0c477f2313c4539ee1182852f2597...
   Template SHA256:   2a7e7dab35d8a34bddf8fa5fd0ae7b46759b9c82962abc...
   → Update this file to match the template version.
```

**Usage:**

```bash
# Run template sync check
pre-commit run check-template-sync --hook-stage manual

# Or run directly
python src/check_template_sync.py --template-path /path/to/template
```

**Perfect for:** Organizations maintaining multiple modules that should share common scaffold files.

### 6. Unit Test Runner

**Runs:** Terraform/OpenTofu unit tests automatically

**Usage:**

```bash
pre-commit run check-tofu-unit-tests --hook-stage manual
```

**Auto-detects test directories:** `tests/`, `test/`, `*_test/`

### 7. Integration Test Runner

**Runs:** Terraform/OpenTofu integration tests

**Usage:**

```bash
pre-commit run check-tofu-integration-tests --hook-stage manual
```

**Auto-detects:** `integration_tests/`, `integration/`, `tests/integration/`

## Provider Support

All hooks work with **any Terraform provider**:

- ✅ AWS, Azure, Google Cloud, Oracle Cloud
- ✅ VMware, Kubernetes, Helm, Docker
- ✅ Datadog, PagerDuty, Cloudflare, Vault
- ✅ 3,000+ providers in the Terraform Registry

## CI/CD Integration

### GitHub Actions

```yaml
name: Terraform Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install pre-commit
      - name: Run hooks
        run: pre-commit run --all-files
```

### GitLab CI

```yaml
terraform-validation:
  stage: validate
  image: python:3.11
  script:
    - pip install pre-commit
    - pre-commit run --all-files
```

### Azure DevOps

```yaml
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'
- script: |
    pip install pre-commit
    pre-commit run --all-files
  displayName: 'Validate Terraform'
```

## What Gets Checked

When you run `git commit`, these hooks automatically check:

1. ✅ Provider configurations use modern patterns
2. ✅ Module versions are consistent across files
3. ✅ Variables and outputs are alphabetically sorted
4. ✅ All taggable resources have required tags with correct case

**Manual test hooks** run separately when you invoke them.

## Documentation

| Document | Purpose |
|----------|---------|
| [INDEX.md](INDEX.md) | Complete overview of all 6 hooks |
| [PROVIDER_CONFIG_PATTERNS.md](PROVIDER_CONFIG_PATTERNS.md) | Provider configuration examples |
| [PROVIDER_CONFIG_MULTI_CLOUD.md](PROVIDER_CONFIG_MULTI_CLOUD.md) | Multi-cloud patterns |
| [TAG_VALIDATION.md](TAG_VALIDATION.md) | Complete tagging guide |
| [README.md](../README.md) | Main repository documentation |

## Benefits

| What You Get | How It Helps |
|--------------|--------------|
| **Consistency** | Enforces standards across your team |
| **Quality** | Catches issues before they reach production |
| **Compliance** | Ensures tagging for cost tracking and governance |
| **Best Practices** | Modern provider patterns enable powerful features |
| **CI/CD Ready** | Integrates seamlessly with pipelines |
| **Multi-Cloud** | Works with any provider, any cloud |

## Next Steps

1. **Install:** Add hooks to your `.pre-commit-config.yaml` (see Step 1 above)
2. **Configure:** Create `.terraform-tags.yaml` for tag validation
3. **Test:** Run `pre-commit run --all-files`
4. **Commit:** Hooks now run automatically on every commit!
5. **Learn More:** Read [INDEX.md](INDEX.md) for complete documentation

## Common Use Cases

### Platform Engineering Team

Enforce standards across multiple teams and projects:

- ✅ Modern provider patterns for module reusability
- ✅ Consistent tagging for cost allocation
- ✅ Sorted code for reduced merge conflicts
- ✅ Version consistency for predictable deployments

### Multi-Cloud Infrastructure

Manage AWS, Azure, and GCP with consistent patterns:

- ✅ Same validation rules across all providers
- ✅ Unified tagging standards (works with AWS tags, GCP labels, etc.)
- ✅ Provider-agnostic module patterns

### Compliance & Governance

Meet organizational requirements:

- ✅ Required tags for compliance (Owner, Environment, CostCenter)
- ✅ Pattern validation for formats (email, ticket IDs)
- ✅ Case-sensitive validation for consistency
- ✅ Automated enforcement in CI/CD

## Getting Help

1. Review [INDEX.md](INDEX.md) for detailed documentation
2. Check [TAG_VALIDATION.md](TAG_VALIDATION.md) for tagging examples
3. See `test/` directory for working examples
4. Open an issue on GitHub for support

---

**Ready? Run:**

```bash
pre-commit run --all-files
```

This will validate your entire Terraform codebase!
