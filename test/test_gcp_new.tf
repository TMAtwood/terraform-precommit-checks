# Example: Google Cloud Platform (GCP) provider - NEW STYLE (CORRECT)
# This should pass the pre-commit hook

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source                = "hashicorp/google"
      version               = "~> 5.0"
      configuration_aliases = [google.main]
    }
  }
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "bucket_name" {
  description = "GCS bucket name"
  type        = string
}

# Resources use the aliased provider
resource "google_storage_bucket" "example" {
  provider = google.main
  name     = var.bucket_name
  location = "US"

  uniform_bucket_level_access = true

  labels = {
    environment = "dev"
    purpose     = "example"
  }
}

output "bucket_url" {
  description = "The URL of the GCS bucket"
  value       = google_storage_bucket.example.url
}
