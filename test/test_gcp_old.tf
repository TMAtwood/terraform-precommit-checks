# Example: Google Cloud Platform (GCP) provider - OLD STYLE
# This should be flagged by the pre-commit hook

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "bucket_name" {
  description = "GCS bucket name"
  type        = string
}

# OLD PATTERN - This will be flagged!
provider "google" {
  project = var.project_id
  region  = "us-central1"
}

resource "google_storage_bucket" "example" {
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
