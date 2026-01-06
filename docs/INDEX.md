# Terraform/OpenTofu Pre-Commit Hooks Documentation

## Overview

This repository provides a comprehensive suite of **provider-agnostic** pre-commit hooks for Terraform and OpenTofu that enforce best practices, consistency, and quality across your infrastructure as code.

## Available Hooks

### 1. Provider Configuration Checker (`check-provider-config`)

**Purpose:** Prevents old-style provider configurations that block `for_each` and `depends_on` at the module level.

**What it detects:**

- Direct `provider "name" { }` blocks in modules
- Enforces `required_providers` with `configuration_aliases` pattern

**Why it matters:** Enables powerful module meta-arguments for dynamic infrastructure patterns.

**Documentation:**

- [PROVIDER_CONFIG_PATTERNS.md](PROVIDER_CONFIG_PATTERNS.md) - Pattern comparison and examples
- [PROVIDER_CONFIG_MULTI_CLOUD.md](PROVIDER_CONFIG_MULTI_CLOUD.md) - Multi-cloud patterns

### 2. Module Version Checker (`check-module-versions`)

**Purpose:** Ensures consistent module versions across all Terraform files.

**What it detects:**

- Conflicting versions for the same module source
- Inconsistent git refs, tags, or commit hashes
- Version mismatches in registry modules

**Why it matters:** Prevents hard-to-debug issues from version conflicts and ensures reproducible deployments.

### 3. TFSort Checker (`check-tfsort`)

**Purpose:** Validates that Terraform variable and output blocks are sorted alphabetically.

**What it detects:**

- Unsorted variables in `variables.tf`
- Unsorted outputs in `outputs.tf`

**Why it matters:** Improves code readability, reduces merge conflicts, and enforces consistency.

### 4. Tag Validation (`check-terraform-tags`)

**Purpose:** Enforces resource tagging standards across all cloud providers.

**What it validates:**

- Required tags are present on all taggable resources
- Tag keys match exact case sensitivity
- Tag values match allowed values lists (case-sensitive)
- Tag values match regex patterns (email, cost center, ticket ID formats)
- Optional tags use correct case when present

**Supports:** AWS (tags), Azure (tags), GCP (labels), Oracle Cloud (freeform_tags), and all other providers.

**Documentation:**

- [TAG_VALIDATION.md](TAG_VALIDATION.md) - Complete guide with configuration examples

### 5. Template Sync Checker (`check-template-sync`)

**Purpose:** Validates repository scaffold files match a reference template directory.

**What it validates:**

- All directories in template exist in repository
- All scaffold files exist in repository
- File content matches exactly (SHA256 hash comparison)
- No missing or modified scaffold files

**Why it matters:** Ensures consistency across multiple modules/repositories. Perfect for organizations maintaining multiple Terraform modules that should share common scaffold files (`.editorconfig`, `.gitignore`, `Jenkinsfile`, `.terraform-tags.yaml`, etc.).

**Stage:** Manual (run with `pre-commit run check-template-sync --hook-stage manual`)

### 6. Unit Test Runner (`check-tofu-unit-tests`)

**Purpose:** Runs Terraform/OpenTofu unit tests automatically.

**What it does:**

- Auto-detects test directories (tests/, test/, *_test/)
- Runs `terraform test` or `tofu test`
- Falls back between tofu and terraform automatically

**Stage:** Manual (run with `pre-commit run check-tofu-unit-tests`)

### 7. Integration Test Runner (`check-tofu-integration-tests`)

**Purpose:** Runs Terraform/OpenTofu integration tests automatically.

**What it does:**

- Auto-detects integration test directories
- Runs comprehensive integration test suites
- Validates end-to-end infrastructure deployments

**Stage:** Manual (run with `pre-commit run check-tofu-integration-tests`)

## Quick Start

### Installation

```bash
# Add to your .pre-commit-config.yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v1.0.0  # Use the latest version
    hooks:
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

# Install hooks
pre-commit install
```

### Running Hooks

```bash
# Run all automatic hooks
pre-commit run --all-files

# Run specific hooks
pre-commit run check-provider-config --all-files
pre-commit run check-module-versions --all-files
pre-commit run check-tfsort --all-files
pre-commit run check-terraform-tags --all-files

# Run manual stage hooks
pre-commit run check-template-sync --hook-stage manual
pre-commit run check-tofu-unit-tests --hook-stage manual
pre-commit run check-tofu-integration-tests --hook-stage manual
```

## Provider Support

All hooks are **provider-agnostic** and work with:

- ✅ AWS, Azure, Google Cloud, Oracle Cloud
- ✅ VMware, Kubernetes, Helm, Docker
- ✅ Datadog, PagerDuty, Cloudflare
- ✅ 3,000+ providers in Terraform Registry

## Documentation Structure

```text
docs/
├── INDEX.md (this file)                    # Overview of all hooks
├── START_HERE.md                           # Quick start guide
├── PROVIDER_CONFIG_PATTERNS.md             # Provider config pattern reference
├── PROVIDER_CONFIG_MULTI_CLOUD.md          # Multi-cloud examples
└── TAG_VALIDATION.md                       # Complete tag validation guide
```

## Integration Patterns

### Git Workflow (Automatic)

Hooks run automatically on `git commit` for staged `.tf` files.

### CI/CD Integration

**GitHub Actions:**

```yaml
- name: Run pre-commit hooks
  run: pre-commit run --all-files
```

**GitLab CI:**

```yaml
terraform-validation:
  script:
    - pip install pre-commit
    - pre-commit run --all-files
```

**Azure DevOps:**

```yaml
- script: |
    pip install pre-commit
    pre-commit run --all-files
  displayName: 'Run Terraform validation'
```

### Direct Execution

Each hook can be run directly:

```bash
# Provider config
python src/check_provider_config.py main.tf

# Module versions
python src/check_module_versions.py main.tf

# TFSort
python src/check_tfsort.py variables.tf

# Tag validation
python src/check_terraform_tags.py --config .terraform-tags.yaml main.tf

# Template sync
python src/check_template_sync.py --template-path /path/to/template

# Unit tests
python src/check_tofu_unit_tests.py

# Integration tests
python src/check_tofu_integration_tests.py
```

## Benefits

| Hook | Prevents | Enables |
|------|----------|---------|
| Provider Config | Modules blocking for_each/depends_on | Dynamic module patterns |
| Module Versions | Version conflicts, drift | Reproducible deployments |
| TFSort | Merge conflicts, inconsistency | Clean, readable code |
| Tag Validation | Missing tags, typos, wrong values | Compliance, cost tracking |
| Template Sync | Repository drift, inconsistent scaffolding | Standardized module structure |
| Unit Tests | Breaking changes | Confident refactoring |
| Integration Tests | Deployment failures | Production readiness |

## Perfect For

- Platform engineering teams
- Multi-cloud organizations
- Large-scale infrastructure projects
- Enforcing best practices and compliance
- CI/CD pipelines
- Team consistency

## Repository Structure

```text
terraform-precommit-checks/
├── src/                                    # Hook implementations
│   ├── check_provider_config.py
│   ├── check_module_versions.py
│   ├── check_tfsort.py
│   ├── check_terraform_tags.py
│   ├── check_template_sync.py
│   ├── check_tofu_unit_tests.py
│   └── check_tofu_integration_tests.py
├── docs/                                   # Documentation
├── test/                                   # Test files and examples
├── examples/                               # Working examples
├── .pre-commit-hooks.yaml                  # Remote hook definitions
├── .pre-commit-config.yaml                 # Local development config
└── README.md                               # Main documentation

```

## Getting Help

1. Check [START_HERE.md](START_HERE.md) for quick start guide
2. Review hook-specific documentation linked above
3. See [README.md](../README.md) for complete installation guide
4. Check test files in `test/` directory for examples
5. Open an issue on GitHub for support

## References

- [Terraform Documentation](https://developer.hashicorp.com/terraform)
- [OpenTofu Documentation](https://opentofu.org/docs/)
- [Pre-commit Framework](https://pre-commit.com/)
- [Terraform Registry](https://registry.terraform.io/)

---

**Ready to get started? See [START_HERE.md](START_HERE.md) for installation and usage guide!**
