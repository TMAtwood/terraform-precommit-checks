# Root Module - Multi-Cloud Deployment
# Demonstrates how to call a multi-cloud module with proper provider configuration

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

# AWS Provider Configuration (multi-region)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"
}

# Azure Provider Configuration
provider "azurerm" {
  alias = "production"
  features {}
  subscription_id = var.azure_subscription_id
}

# Google Cloud Provider Configuration
provider "google" {
  alias   = "production"
  project = var.gcp_project_id
  region  = "us-central1"
}

# Oracle Cloud Provider Configuration
provider "oci" {
  alias            = "production"
  tenancy_ocid     = var.oci_tenancy_ocid
  user_ocid        = var.oci_user_ocid
  fingerprint      = var.oci_fingerprint
  private_key_path = var.oci_private_key_path
  region           = var.oci_region
}

# Supporting Azure Resources
resource "azurerm_resource_group" "main" {
  provider = azurerm.production
  name     = "multi-cloud-storage"
  location = "East US"

  tags = {
    environment = "production"
    managed_by  = "terraform"
  }
}

# Example 1: Deploy storage to all clouds for different environments
# Now possible with for_each!
module "environment_storage" {
  source   = "./modules/multi-cloud-storage"
  for_each = var.environments

  providers = {
    aws.primary    = aws.us_east_1
    aws.backup     = aws.us_west_2
    azurerm.main   = azurerm.production
    google.main    = google.production
    oci.main       = oci.production
  }

  resource_prefix             = "${each.key}-app"
  azure_resource_group_name   = azurerm_resource_group.main.name
  gcp_project_id              = var.gcp_project_id
  oci_compartment_id          = var.oci_compartment_id
}

# Example 2: Deploy with dependency control
# Now possible with depends_on!
module "backup_storage" {
  source = "./modules/multi-cloud-storage"

  providers = {
    aws.primary    = aws.us_east_1
    aws.backup     = aws.us_west_2
    azurerm.main   = azurerm.production
    google.main    = google.production
    oci.main       = oci.production
  }

  # Can now use depends_on at module level!
  depends_on = [
    azurerm_resource_group.main,
    module.environment_storage
  ]

  resource_prefix             = "backup"
  azure_resource_group_name   = azurerm_resource_group.main.name
  gcp_project_id              = var.gcp_project_id
  oci_compartment_id          = var.oci_compartment_id
}

# Example 3: Dynamic multi-cloud deployment
# Combining for_each and depends_on!
module "region_specific_storage" {
  source   = "./modules/multi-cloud-storage"
  for_each = var.regional_configs

  providers = {
    aws.primary    = aws.us_east_1
    aws.backup     = aws.us_west_2
    azurerm.main   = azurerm.production
    google.main    = google.production
    oci.main       = oci.production
  }

  depends_on = [module.backup_storage]

  resource_prefix             = "${each.key}-regional"
  azure_resource_group_name   = azurerm_resource_group.main.name
  gcp_project_id              = var.gcp_project_id
  oci_compartment_id          = var.oci_compartment_id
}

# Variables
variable "environments" {
  description = "Environments to deploy across all clouds"
  type = map(object({
    name = string
  }))
  default = {
    dev = {
      name = "development"
    }
    staging = {
      name = "staging"
    }
    prod = {
      name = "production"
    }
  }
}

variable "regional_configs" {
  description = "Regional deployment configurations"
  type = map(object({
    name = string
  }))
  default = {
    north_america = {
      name = "na"
    }
    europe = {
      name = "eu"
    }
    asia_pacific = {
      name = "apac"
    }
  }
}

# AWS Variables
# (No additional variables needed - using defaults from provider blocks)

# Azure Variables
variable "azure_subscription_id" {
  description = "Azure subscription ID"
  type        = string
  sensitive   = true
}

# GCP Variables
variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

# OCI Variables
variable "oci_tenancy_ocid" {
  description = "OCI tenancy OCID"
  type        = string
  sensitive   = true
}

variable "oci_user_ocid" {
  description = "OCI user OCID"
  type        = string
  sensitive   = true
}

variable "oci_fingerprint" {
  description = "OCI key fingerprint"
  type        = string
  sensitive   = true
}

variable "oci_private_key_path" {
  description = "Path to OCI private key"
  type        = string
  sensitive   = true
}

variable "oci_region" {
  description = "OCI region"
  type        = string
  default     = "us-ashburn-1"
}

variable "oci_compartment_id" {
  description = "OCI compartment ID"
  type        = string
}

# Outputs
output "all_environment_storage" {
  description = "Storage resources for all environments across all clouds"
  value = {
    for env, module in module.environment_storage :
    env => module.storage_summary
  }
}

output "backup_storage" {
  description = "Backup storage across all clouds"
  value       = module.backup_storage.storage_summary
}

output "regional_storage" {
  description = "Regional storage deployments"
  value = {
    for region, module in module.region_specific_storage :
    region => module.storage_summary
  }
}

output "deployment_summary" {
  description = "Complete deployment summary"
  value = {
    total_environments = length(var.environments)
    total_regions      = length(var.regional_configs)
    clouds_deployed    = ["aws", "azure", "gcp", "oracle"]
    features_enabled   = ["for_each", "depends_on", "multi-provider"]
  }
}
