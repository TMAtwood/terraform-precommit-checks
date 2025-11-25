# Multi-Cloud Provider Support

This pre-commit hook is **completely provider-agnostic** and works with **ANY** Terraform/OpenTofu provider, including:

## Supported Cloud Providers

✅ **AWS** (amazon web services)
- Provider: `aws`
- Source: `hashicorp/aws`

✅ **Azure** (microsoft azure)
- Provider: `azurerm`
- Source: `hashicorp/azurerm`

✅ **GCP** (google cloud platform)
- Provider: `google` / `google-beta`
- Source: `hashicorp/google`

✅ **Oracle Cloud** (OCI)
- Provider: `oci`
- Source: `oracle/oci`

✅ **Alibaba Cloud**
- Provider: `alicloud`
- Source: `aliyun/alicloud`

✅ **IBM Cloud**
- Provider: `ibm`
- Source: `IBM-Cloud/ibm`

✅ **DigitalOcean**
- Provider: `digitalocean`
- Source: `digitalocean/digitalocean`

✅ **VMware vSphere**
- Provider: `vsphere`
- Source: `hashicorp/vsphere`

✅ **Kubernetes**
- Provider: `kubernetes`
- Source: `hashicorp/kubernetes`

✅ **Helm**
- Provider: `helm`
- Source: `hashicorp/helm`

...and **hundreds more** in the [Terraform Registry](https://registry.terraform.io/browse/providers)!

## How It Works

The hook detects the pattern `provider "ANY_NAME" {` and validates that it follows the new configuration style. It doesn't matter which cloud provider you're using - the same rules apply.

## Multi-Cloud Examples

### AWS + Azure

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

resource "aws_s3_bucket" "backup" {
  provider = aws.main
  bucket   = var.bucket_name
}

resource "azurerm_storage_account" "primary" {
  provider            = azurerm.main
  name                = var.storage_name
  resource_group_name = var.resource_group
  location            = var.location
  account_tier        = "Standard"
}
```

**Usage:**
```hcl
provider "aws" {
  alias  = "us_east"
  region = "us-east-1"
}

provider "azurerm" {
  alias = "prod"
  features {}
}

module "hybrid_storage" {
  source   = "./modules/hybrid-storage"
  for_each = var.applications  # ✅ Now works!

  providers = {
    aws.main     = aws.us_east
    azurerm.main = azurerm.prod
  }
}
```

### GCP + Oracle Cloud

**Module:**
```hcl
terraform {
  required_providers {
    google = {
      source                = "hashicorp/google"
      version               = "~> 5.0"
      configuration_aliases = [google.main]
    }
    oci = {
      source                = "oracle/oci"
      version               = "~> 5.0"
      configuration_aliases = [oci.main]
    }
  }
}

resource "google_storage_bucket" "data" {
  provider = google.main
  name     = var.bucket_name
  location = "US"
}

resource "oci_objectstorage_bucket" "backup" {
  provider       = oci.main
  compartment_id = var.compartment_id
  name           = var.bucket_name
  namespace      = var.namespace
}
```

### Kubernetes + Helm

**Module:**
```hcl
terraform {
  required_providers {
    kubernetes = {
      source                = "hashicorp/kubernetes"
      version               = "~> 2.0"
      configuration_aliases = [kubernetes.main]
    }
    helm = {
      source                = "hashicorp/helm"
      version               = "~> 2.0"
      configuration_aliases = [helm.main]
    }
  }
}

resource "kubernetes_namespace" "app" {
  provider = kubernetes.main
  metadata {
    name = var.namespace
  }
}

resource "helm_release" "app" {
  provider   = helm.main
  name       = var.app_name
  chart      = var.chart_name
  namespace  = kubernetes_namespace.app.metadata[0].name
}
```

## Testing Different Providers

The repository includes test files for multiple cloud providers:

```bash
# Test Azure
python check_provider_config.py test_azure_old.tf

# Test GCP
python check_provider_config.py test_gcp_old.tf

# Test Oracle Cloud
python check_provider_config.py test_oci_old.tf

# Test AWS
python check_provider_config.py test_old_style.tf

# Test all at once
python check_provider_config.py test_*_old.tf
```

## Provider-Specific Notes

### AWS
- Commonly uses multiple regions with aliases
- Example: `aws.us-east-1`, `aws.us-west-2`

### Azure (azurerm)
- Often uses `features {}` block (this is fine!)
- Example aliases: `azurerm.production`, `azurerm.dev`

### GCP (google)
- May use both `google` and `google-beta` providers
- Example aliases: `google.main`, `google-beta.main`

### Oracle Cloud (oci)
- Requires multiple authentication parameters
- Example aliases: `oci.home`, `oci.region1`

### Multi-Region / Multi-Account Deployments

The new pattern enables powerful multi-region and multi-account patterns:

```hcl
# Deploy to 5 AWS regions with one module call
module "global_deployment" {
  source   = "./modules/app"
  for_each = toset([
    "us-east-1",
    "us-west-2",
    "eu-west-1",
    "ap-southeast-1",
    "sa-east-1"
  ])

  providers = {
    aws.main = aws[each.key]
  }
}
```

## Why Provider-Agnostic Matters

1. **Consistency**: Same pattern works across all clouds
2. **Portability**: Easy to migrate between providers
3. **Multi-cloud**: Mix and match providers as needed
4. **Future-proof**: Works with new providers automatically

## Detection Examples

The hook will catch old patterns for ANY provider:

```hcl
# ❌ All of these will be flagged
provider "aws" { ... }
provider "azurerm" { ... }
provider "google" { ... }
provider "oci" { ... }
provider "kubernetes" { ... }
provider "datadog" { ... }
provider "cloudflare" { ... }
provider "vault" { ... }
# ... and hundreds more
```

And require the new pattern:

```hcl
# ✅ Correct for ALL providers
terraform {
  required_providers {
    <any_provider> = {
      source                = "<provider_source>"
      version               = "<version>"
      configuration_aliases = [<provider>.main]
    }
  }
}
```

## Real-World Multi-Cloud Use Cases

1. **Hybrid Cloud**: Primary workload in AWS, backup in Azure
2. **Data Residency**: Different regions for compliance
3. **Cost Optimization**: Use cheapest provider per region
4. **Vendor Diversification**: Reduce single-vendor risk
5. **Best-of-Breed**: Use best service from each provider

## Summary

This tool works with:
- ✅ All major cloud providers (AWS, Azure, GCP, Oracle)
- ✅ All minor cloud providers (DigitalOcean, Linode, etc.)
- ✅ Infrastructure providers (VMware, OpenStack)
- ✅ Service providers (Datadog, PagerDuty, Cloudflare)
- ✅ Platform providers (Kubernetes, Helm, Docker)
- ✅ Custom/private providers

**The pattern is universal - if it's a Terraform provider, this hook supports it!**
