# Example: Oracle Cloud Infrastructure (OCI) provider - OLD STYLE
# This should be flagged by the pre-commit hook

variable "compartment_id" {
  description = "OCI compartment ID"
  type        = string
}

variable "bucket_name" {
  description = "Object storage bucket name"
  type        = string
}

# OLD PATTERN - This will be flagged!
provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

data "oci_objectstorage_namespace" "example" {
  compartment_id = var.compartment_id
}

resource "oci_objectstorage_bucket" "example" {
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
