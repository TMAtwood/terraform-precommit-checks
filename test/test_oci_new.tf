# Example: Oracle Cloud Infrastructure (OCI) provider - NEW STYLE (CORRECT)
# This should pass the pre-commit hook

terraform {
  required_version = ">= 1.5"

  required_providers {
    oci = {
      source                = "oracle/oci"
      version               = "~> 5.0"
      configuration_aliases = [oci.main]
    }
  }
}

variable "compartment_id" {
  description = "OCI compartment ID"
  type        = string
}

variable "bucket_name" {
  description = "Object storage bucket name"
  type        = string
}

# Data sources and resources use the aliased provider
data "oci_objectstorage_namespace" "example" {
  provider       = oci.main
  compartment_id = var.compartment_id
}

resource "oci_objectstorage_bucket" "example" {
  provider       = oci.main
  compartment_id = var.compartment_id
  name           = var.bucket_name
  namespace      = data.oci_objectstorage_namespace.example.namespace

  freeform_tags = {
    "Environment" = "dev"
    "Purpose"     = "example"
  }
}

output "bucket_name" {
  description = "The name of the object storage bucket"
  value       = oci_objectstorage_bucket.example.name
}
