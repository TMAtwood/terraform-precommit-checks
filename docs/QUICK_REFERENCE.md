# Quick Reference: Provider Configuration Patterns

## Why This Matters

Old-style provider configurations **block** the use of `for_each` and `depends_on` at the module level, which are essential for:
- Creating multiple module instances dynamically
- Controlling module execution order
- Building scalable infrastructure as code

## Pattern Comparison

### ❌ OLD PATTERN (Blocked Features)

```hcl
# modules/example/main.tf

# This prevents for_each and depends_on!
provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "example" {
  bucket = var.bucket_name
}
```

**Result when calling module:**
```hcl
module "example" {
  source = "./modules/example"

  for_each = var.instances  # ❌ ERROR: Can't use for_each
  depends_on = [aws_iam_role.example]  # ❌ ERROR: Can't use depends_on
}
```

### ✅ NEW PATTERN (Full Features)

```hcl
# modules/example/main.tf

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

**Result when calling module:**
```hcl
provider "aws" {
  alias  = "primary"
  region = "us-east-1"
}

module "example" {
  source = "./modules/example"

  providers = {
    aws.main = aws.primary
  }

  for_each   = var.instances  # ✅ Works!
  depends_on = [aws_iam_role.example]  # ✅ Works!
}
```

## Common Scenarios

### Single Provider

**Module:**
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

**Usage:**
```hcl
provider "aws" {
  alias  = "primary"
  region = "us-east-1"
}

module "example" {
  source = "./modules/example"

  providers = {
    aws.main = aws.primary
  }
}
```

### Multiple Providers (Same Type)

**Module:**
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
      configuration_aliases = [
        aws.primary,
        aws.secondary
      ]
    }
  }
}
```

**Usage:**
```hcl
provider "aws" {
  alias  = "us_east"
  region = "us-east-1"
}

provider "aws" {
  alias  = "us_west"
  region = "us-west-2"
}

module "multi_region" {
  source = "./modules/multi-region"

  providers = {
    aws.primary   = aws.us_east
    aws.secondary = aws.us_west
  }
}
```

### Multiple Providers (Different Types)

**Module:**
```hcl
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.0"
      configuration_aliases = [aws.main]
    }
    azurerm = {
      source                = "hashicorp/azurerm"
      version               = "~> 3.0"
      configuration_aliases = [azurerm.main]
    }
  }
}
```

**Usage:**
```hcl
provider "aws" {
  alias  = "primary"
  region = "us-east-1"
}

provider "azurerm" {
  alias = "primary"
  features {}
}

module "multi_cloud" {
  source = "./modules/multi-cloud"

  providers = {
    aws.main     = aws.primary
    azurerm.main = azurerm.primary
  }
}
```

## Migration Checklist

- [ ] Identify all modules with direct `provider` blocks
- [ ] Add `required_providers` with `configuration_aliases`
- [ ] Update resource references to use provider aliases
- [ ] Update module calls to pass providers via `providers` argument
- [ ] Test with `terraform plan`
- [ ] Run pre-commit hook: `pre-commit run check-provider-config --all-files`

## Benefits

| Feature | Old Pattern | New Pattern |
|---------|-------------|-------------|
| `for_each` on modules | ❌ No | ✅ Yes |
| `depends_on` on modules | ❌ No | ✅ Yes |
| Multi-region deployment | ⚠️ Limited | ✅ Full support |
| Provider version control | ⚠️ Implicit | ✅ Explicit |
| Module reusability | ⚠️ Limited | ✅ High |

## References

- [Terraform Providers in Modules](https://developer.hashicorp.com/terraform/language/modules/develop/providers)
- [Module Meta-Arguments](https://developer.hashicorp.com/terraform/language/meta-arguments/module-providers)
- [Configuration Aliases](https://developer.hashicorp.com/terraform/language/providers/configuration#alias-multiple-provider-configurations)
