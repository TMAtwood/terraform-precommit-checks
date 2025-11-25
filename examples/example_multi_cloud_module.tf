# Multi-Cloud Module Example - NEW PATTERN
# Demonstrates correct provider configuration for AWS, Azure, GCP, and Oracle Cloud

terraform {
  required_version = ">= 1.5"

  required_providers {
    # AWS Provider
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
      configuration_aliases = [
        aws.primary,
        aws.backup
      ]
    }

    # Azure Provider
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
      configuration_aliases = [
        azurerm.main
      ]
    }

    # Google Cloud Provider
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
      configuration_aliases = [
        google.main
      ]
    }

    # Oracle Cloud Infrastructure Provider
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
      configuration_aliases = [
        oci.main
      ]
    }
  }
}

# Variables
variable "resource_prefix" {
  description = "Prefix for all resources"
  type        = string
}

variable "azure_resource_group_name" {
  description = "Azure resource group name"
  type        = string
}

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "oci_compartment_id" {
  description = "OCI compartment ID"
  type        = string
}

# AWS Resources (multi-region)
resource "aws_s3_bucket" "primary" {
  provider = aws.primary
  bucket   = "${var.resource_prefix}-primary"

  tags = {
    Environment = "production"
    Region      = "primary"
  }
}

resource "aws_s3_bucket" "backup" {
  provider = aws.backup
  bucket   = "${var.resource_prefix}-backup"

  tags = {
    Environment = "production"
    Region      = "backup"
  }
}

# Azure Resources
resource "azurerm_storage_account" "main" {
  provider                 = azurerm.main
  name                     = "${var.resource_prefix}storage"
  resource_group_name      = var.azure_resource_group_name
  location                 = "East US"
  account_tier             = "Standard"
  account_replication_type = "GRS"

  tags = {
    environment = "production"
  }
}

resource "azurerm_storage_container" "data" {
  provider              = azurerm.main
  name                  = "data"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Google Cloud Resources
resource "google_storage_bucket" "main" {
  provider = google.main
  name     = "${var.resource_prefix}-gcp-bucket"
  location = "US"

  uniform_bucket_level_access = true

  labels = {
    environment = "production"
  }
}

# Oracle Cloud Resources
resource "oci_objectstorage_bucket" "main" {
  provider       = oci.main
  compartment_id = var.oci_compartment_id
  name           = "${var.resource_prefix}-oci-bucket"
  namespace      = data.oci_objectstorage_namespace.main.namespace

  freeform_tags = {
    "Environment" = "production"
  }
}

data "oci_objectstorage_namespace" "main" {
  provider       = oci.main
  compartment_id = var.oci_compartment_id
}

# Outputs
output "aws_primary_bucket" {
  description = "AWS primary S3 bucket name"
  value       = aws_s3_bucket.primary.id
}

output "aws_backup_bucket" {
  description = "AWS backup S3 bucket name"
  value       = aws_s3_bucket.backup.id
}

output "azure_storage_account" {
  description = "Azure storage account name"
  value       = azurerm_storage_account.main.name
}

output "gcp_bucket" {
  description = "GCP storage bucket name"
  value       = google_storage_bucket.main.name
}

output "oci_bucket" {
  description = "OCI object storage bucket name"
  value       = oci_objectstorage_bucket.main.name
}

output "storage_summary" {
  description = "Summary of all storage resources across clouds"
  value = {
    aws = {
      primary = aws_s3_bucket.primary.id
      backup  = aws_s3_bucket.backup.id
    }
    azure = {
      account   = azurerm_storage_account.main.name
      container = azurerm_storage_container.data.name
    }
    gcp = {
      bucket = google_storage_bucket.main.name
    }
    oracle = {
      bucket = oci_objectstorage_bucket.main.name
    }
  }
}
