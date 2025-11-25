# Terraform Tag Validation Hook

This hook validates that Terraform/OpenTofu resources have required tags with correct case sensitivity and allowed values. It works universally with any Terraform provider (AWS, Azure, GCP, Oracle Cloud, and 3,000+ others).

## Features

- **Required Tags**: Enforce that specific tags are present on all taggable resources
- **Case Sensitivity**: Validate that tag keys match exact case (e.g., "Environment" not "environment")
- **Allowed Values**: Restrict tag values to a predefined list with case-sensitive validation
- **Optional Tags**: Validate case sensitivity for optional tags when present
- **Multi-Provider**: Supports AWS (tags), Azure (tags), GCP (labels), Oracle Cloud, and all other providers
- **Flexible Configuration**: Use YAML config file or command-line JSON arguments

## Quick Start

### 1. Create Configuration File

Create a `.terraform-tags.yaml` file in your repository root:

```yaml
required_tags:
  - name: Environment
    allowed_values:
      - Development
      - Staging
      - Production

  - name: Owner  # Any non-empty value allowed

  - name: CostCenter  # Any non-empty value allowed

optional_tags:
  - name: Project
  - name: Description
```

### 2. Add to Pre-Commit Configuration

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v1.0.0  # Use the latest version
    hooks:
      - id: check-terraform-tags
        args: [--config, .terraform-tags.yaml]
```

### 3. Run the Hook

```bash
# Run on all .tf files
pre-commit run check-terraform-tags --all-files

# Run on specific files
pre-commit run check-terraform-tags --files main.tf variables.tf
```

## Configuration

### YAML Configuration File

The most flexible option is to use a YAML configuration file:

```yaml
# .terraform-tags.yaml
required_tags:
  # Tag with restricted values (exact match)
  - name: Environment
    allowed_values:
      - Development
      - Staging
      - Production

  # Tag with regex pattern validation (email format)
  - name: Owner
    pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

  # Tag with pattern validation (cost center format: CC-####)
  - name: CostCenter
    pattern: "^CC-[0-9]{4}$"

  # Tag with pattern validation (ticket ID: PROJECT-###)
  - name: TicketID
    pattern: "^[A-Z]+-[0-9]+$"

optional_tags:
  # These are checked for case sensitivity if present
  - name: Project
  - name: Description
  - name: Team

# Optional: Override default taggable resources
# If not specified, uses built-in comprehensive lists for AWS, Azure, GCP, OCI
taggable_resources:
  aws:
    - aws_instance
    - aws_s3_bucket
    - aws_vpc
    # Add more...

  azurerm:
    - azurerm_resource_group
    - azurerm_virtual_machine
    # Add more...
```

### Command-Line Arguments

You can also configure via command-line JSON arguments:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/TMAtwood/terraform-precommit-checks
    rev: v1.0.0
    hooks:
      - id: check-terraform-tags
        args:
          - --required-tags
          - '[{"name":"Environment","allowed_values":["Development","Staging","Production"]},{"name":"Owner"}]'
          - --optional-tags
          - '[{"name":"Project"},{"name":"Description"}]'
```

### Direct Script Execution

```bash
# Using config file
python src/check_terraform_tags.py --config .terraform-tags.yaml main.tf

# Using command-line args
python src/check_terraform_tags.py \
  --required-tags '[{"name":"Environment","allowed_values":["Dev","Prod"]},{"name":"Owner"}]' \
  --optional-tags '[{"name":"Project"}]' \
  main.tf
```

## Validation Rules

### Required Tags

1. **Must be present** on all taggable resources
2. **Case-sensitive keys**: "Environment" ≠ "environment"
3. **Non-empty values**: Tag value cannot be empty or whitespace
4. **Allowed values** (if specified): Value must match exactly (case-sensitive)

### Optional Tags

1. **Not required** to be present
2. **Case-sensitive keys** (if present): "Project" ≠ "project"
3. **No value validation**: Any value allowed

### Pattern Validation

Pattern validation uses regular expressions to enforce specific formats for tag values:

1. **Use `pattern` for flexible validation** - Define a regex pattern that tag values must match
2. **Common patterns**:
   - **Email**: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
   - **Cost Center** (CC-####): `^CC-[0-9]{4}$`
   - **Ticket ID** (PROJ-###): `^[A-Z]+-[0-9]+$`
   - **Date** (YYYY-MM-DD): `^[0-9]{4}-[0-9]{2}-[0-9]{2}$`
   - **Version** (v#.#.#): `^v[0-9]+\.[0-9]+\.[0-9]+$`
3. **Pattern vs allowed_values**: Use `allowed_values` for exact matches, `pattern` for format validation
4. **Invalid patterns** are caught and reported clearly

**Example configuration:**

```yaml
required_tags:
  # Exact match validation
  - name: Environment
    allowed_values: [Development, Staging, Production]

  # Pattern validation for email format
  - name: Owner
    pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

  # Pattern validation for cost center format
  - name: CostCenter
    pattern: "^CC-[0-9]{4}$"
```

**Pattern validation examples:**

```hcl
# ✅ PASS - Matches email pattern
tags = {
  Owner = "admin@example.com"
}

# ❌ FAIL - Does not match email pattern
tags = {
  Owner = "admin"  # Missing @domain
}

# ✅ PASS - Matches CC-#### pattern
tags = {
  CostCenter = "CC-1234"
}

# ❌ FAIL - Does not match CC-#### pattern
tags = {
  CostCenter = "1234"  # Missing CC- prefix
}
```

### Taggable Resources

The hook includes comprehensive built-in lists of taggable resources for:

- **AWS**: 100+ resources (aws_instance, aws_s3_bucket, aws_vpc, etc.)
- **Azure**: 40+ resources (azurerm_resource_group, azurerm_virtual_machine, etc.)
- **GCP**: 30+ resources (google_compute_instance, google_storage_bucket, etc.) - uses `labels` instead of `tags`
- **Oracle Cloud**: 10+ resources (oci_core_instance, oci_core_vcn, etc.)

You can extend or override these lists in your configuration file.

## Examples

### Valid Terraform Code

```hcl
# AWS resource with all required tags
resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  tags = {
    Environment = "Production"  # Correct case, valid value
    Owner       = "team-a@example.com"  # Correct case, any value
    CostCenter  = "CC-1234"  # Correct case, any value
    Project     = "WebApp"  # Optional tag with correct case
  }
}

# Azure resource with required tags
resource "azurerm_resource_group" "main" {
  name     = "my-rg"
  location = "East US"

  tags = {
    Environment = "Development"
    Owner       = "azure-team@example.com"
    CostCenter  = "CC-5678"
  }
}

# GCP resource with labels (not tags)
resource "google_compute_instance" "app" {
  name         = "app-server"
  machine_type = "n1-standard-1"

  labels = {
    Environment = "Staging"
    Owner       = "gcp-team@example.com"
    CostCenter  = "CC-9999"
  }
}
```

### Invalid Terraform Code

```hcl
# FAIL: Missing required tag (CostCenter)
resource "aws_instance" "bad1" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  tags = {
    Environment = "Production"
    Owner       = "team@example.com"
    # Missing: CostCenter
  }
}

# FAIL: Wrong case for tag key
resource "aws_vpc" "bad2" {
  cidr_block = "10.0.0.0/16"

  tags = {
    environment = "Production"  # Should be "Environment"
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
  }
}

# FAIL: Invalid tag value (not in allowed list)
resource "aws_s3_bucket" "bad3" {
  bucket = "my-bucket"

  tags = {
    Environment = "Testing"  # Not in allowed values
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
  }
}

# FAIL: Empty tag value
resource "aws_security_group" "bad4" {
  name = "my-sg"

  tags = {
    Environment = "Production"
    Owner       = ""  # Empty value not allowed
    CostCenter  = "CC-1234"
  }
}

# FAIL: Optional tag with wrong case
resource "aws_ebs_volume" "bad5" {
  availability_zone = "us-west-2a"
  size              = 10

  tags = {
    Environment = "Production"
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
    project     = "MyProject"  # Should be "Project"
  }
}

# FAIL: No tags on taggable resource
resource "aws_db_instance" "bad6" {
  identifier        = "mydb"
  engine            = "postgres"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  # Missing tags entirely
}
```

## Error Output

When violations are detected, the hook provides clear error messages:

```
================================================================================
❌ TERRAFORM TAG VALIDATION FAILED
================================================================================

📁 File: main.tf
📍 Line: 15
🏷️  Resource: aws_instance.bad1
⚠️  Required tag 'CostCenter' is missing.

📁 File: main.tf
📍 Line: 25
🏷️  Resource: aws_vpc.bad2
⚠️  Required tag 'Environment' has incorrect case. Found 'environment' but expected 'Environment'.

📁 File: main.tf
📍 Line: 35
🏷️  Resource: aws_s3_bucket.bad3
⚠️  Tag 'Environment' has invalid value 'Testing'. Allowed values: ['Development', 'Staging', 'Production'].

================================================================================
💡 TAG REQUIREMENTS:
================================================================================

Required tags:
  • Environment (allowed: ['Development', 'Staging', 'Production'])
  • Owner (any non-empty value)
  • CostCenter (any non-empty value)

Optional tags (case-sensitive if used):
  • Project
  • Description
```

## Dynamic Tags

The hook skips validation for resources using dynamic tag assignments:

```hcl
# These will be skipped (can't validate dynamic tags)
resource "aws_instance" "dynamic" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  # Using merge() - skipped
  tags = merge(var.common_tags, {
    Name = "my-instance"
  })
}

resource "aws_vpc" "from_var" {
  cidr_block = "10.0.0.0/16"

  # Using variable - skipped
  tags = var.vpc_tags
}

resource "aws_subnet" "from_local" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"

  # Using local - skipped
  tags = local.subnet_tags
}
```

## Provider-Specific Notes

### AWS
- Uses `tags` attribute
- Most resources support tags
- Some resources use `tags_all` (automatically handled)

### Azure (azurerm)
- Uses `tags` attribute
- Tags are case-sensitive
- Maximum 50 tags per resource

### GCP (google)
- Uses `labels` attribute (not `tags`)
- Labels are key-value pairs
- Maximum 64 labels per resource

### Oracle Cloud (oci)
- Uses `freeform_tags` and `defined_tags`
- Currently validates `freeform_tags` (similar to AWS tags)

## Best Practices

### 1. Start with Core Tags

Begin with essential tags that provide value:

```yaml
required_tags:
  - name: Environment
    allowed_values: [Development, Staging, Production]
  - name: Owner
  - name: CostCenter
```

### 2. Use Consistent Case

Choose a casing convention and stick to it:

```yaml
# PascalCase (recommended)
- name: CostCenter
- name: ProjectName

# snake_case
- name: cost_center
- name: project_name

# kebab-case
- name: cost-center
- name: project-name
```

### 3. Validate Critical Values

Use `allowed_values` for tags that affect billing, compliance, or automation:

```yaml
required_tags:
  - name: Environment
    allowed_values: [Development, Staging, Production]
  - name: Compliance
    allowed_values: [PCI-DSS, HIPAA, SOC2, None]
  - name: Backup
    allowed_values: [Daily, Weekly, None]
```

### 4. Document Tag Meanings

Add comments to your config file:

```yaml
required_tags:
  # Deployment environment - affects resource naming and configuration
  - name: Environment
    allowed_values: [Development, Staging, Production]

  # Team/person responsible for the resource
  - name: Owner

  # Finance tracking code for chargebacks
  - name: CostCenter
```

### 5. Use Optional Tags for Metadata

```yaml
optional_tags:
  - name: Project        # Project or application name
  - name: Description    # Human-readable description
  - name: ManagedBy      # Tool managing the resource (e.g., Terraform)
  - name: Repository     # Git repository URL
```

## Troubleshooting

### Hook Not Running

Check that:
1. Hook is installed: `pre-commit install`
2. Hook is in `.pre-commit-config.yaml`
3. Files match pattern (`.tf` files)

### PyYAML Not Found

Install PyYAML:
```bash
pip install PyYAML>=6.0
```

Or use JSON arguments instead:
```yaml
hooks:
  - id: check-terraform-tags
    args:
      - --required-tags
      - '[{"name":"Environment","allowed_values":["Dev","Prod"]}]'
```

### False Positives

If resources are incorrectly flagged as taggable:

1. Remove them from the taggable resources list in your config:

```yaml
taggable_resources:
  aws:
    - aws_instance
    - aws_s3_bucket
    # Remove resources that shouldn't be tagged
```

2. Or use `exclude` in pre-commit config:

```yaml
hooks:
  - id: check-terraform-tags
    exclude: ^modules/legacy/
```

### Dynamic Tags Not Detected

The hook skips resources using `merge()`, `var.`, or `local.` for tags. If you need to validate these, consider using static tags with dynamic values:

```hcl
# Instead of:
tags = var.tags

# Use:
tags = {
  Environment = var.environment
  Owner       = var.owner
  CostCenter  = var.cost_center
}
```

## Integration with CI/CD

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
        run: pip install pre-commit PyYAML
      - name: Run tag validation
        run: pre-commit run check-terraform-tags --all-files
```

### GitLab CI

```yaml
terraform-tag-validation:
  stage: validate
  image: python:3.11
  script:
    - pip install pre-commit PyYAML
    - pre-commit run check-terraform-tags --all-files
```

### Azure DevOps

```yaml
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'
- script: |
    pip install pre-commit PyYAML
    pre-commit run check-terraform-tags --all-files
  displayName: 'Validate Terraform Tags'
```

## Advanced Configuration

### Different Tags Per Provider

You can create provider-specific tag requirements by using multiple config files:

```bash
# AWS-specific tags
check-terraform-tags --config .terraform-tags-aws.yaml aws/*.tf

# Azure-specific tags
check-terraform-tags --config .terraform-tags-azure.yaml azure/*.tf
```

### Pattern-Based Value Validation

While `allowed_values` checks exact matches, you can also validate patterns:

```yaml
required_tags:
  - name: CostCenter
    # In your validation, you could add regex pattern support
    # pattern: "^CC-[0-9]{4}$"
```

*Note: Pattern validation is not yet implemented but could be added as a feature request.*

### Tag Inheritance

For complex infrastructures, consider using a tag generation module:

```hcl
# modules/tags/main.tf
locals {
  required_tags = {
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
  }
}

output "tags" {
  value = merge(
    local.required_tags,
    var.additional_tags
  )
}

# Then use in resources:
resource "aws_instance" "web" {
  # ... other config ...
  tags = module.tags.tags
}
```

## Contributing

Found a resource type that should be tagged but isn't in our list? Please open an issue or PR!

## See Also

- [Main README](../README.md) - Repository overview
- [Provider Configuration Checker](../README.md#provider-configuration-checker) - Validate provider patterns
- [Module Version Checker](../README.md#module-version-checker) - Check module version consistency
- [TFSort Checker](../README.md#tfsort-checker) - Validate file sorting
