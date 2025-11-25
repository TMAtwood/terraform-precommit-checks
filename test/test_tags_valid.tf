# Test case: Valid tags - should PASS
# All required tags present with correct case and valid values

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Valid: All required tags present with correct values
resource "aws_instance" "valid_all_tags" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  tags = {
    Environment = "Production"
    Owner       = "john.doe@example.com"
    CostCenter  = "CC-1234"
  }
}

# Valid: Required tags + optional tags with correct case
resource "aws_vpc" "valid_with_optional" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Environment = "Development"
    Owner       = "team-a@example.com"
    CostCenter  = "CC-5678"
    Project     = "MyProject"
    Description = "Test VPC"
  }
}

# Valid: Azure resource with correct tags
resource "azurerm_resource_group" "valid_azure" {
  name     = "example-rg"
  location = "East US"

  tags = {
    Environment = "Staging"
    Owner       = "azure-team@example.com"
    CostCenter  = "CC-9999"
  }
}

# Valid: GCP resource with labels (not tags)
# Note: GCP uses "labels" instead of "tags", but same validation rules apply
resource "google_compute_instance" "valid_gcp" {
  name         = "test-instance"
  machine_type = "n1-standard-1"
  zone         = "us-central1-a"

  labels = {
    Environment = "Production"
    Owner       = "gcp-team@example.com"
    CostCenter  = "CC-1111"
  }
}

# Non-taggable resource - should be ignored
resource "aws_iam_policy_document" "non_taggable" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
    ]
    resources = ["*"]
  }
}
