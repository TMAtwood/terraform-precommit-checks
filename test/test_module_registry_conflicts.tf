# Test file for REGISTRY MODULE version conflicts
# Tests Terraform Registry module patterns

# Scenario 1: AWS VPC module with different versions - CONFLICT
module "vpc_development" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "dev-vpc"
  cidr = "10.0.0.0/16"
}

module "vpc_staging" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.0"

  name = "staging-vpc"
  cidr = "10.1.0.0/16"
}

# Scenario 2: Azure network module with different versions - CONFLICT
module "azure_network_east" {
  source  = "Azure/network/azurerm"
  version = "3.5.0"

  resource_group_name = "rg-east"
}

module "azure_network_west" {
  source  = "Azure/network/azurerm"
  version = "4.0.0"

  resource_group_name = "rg-west"
}

# Scenario 3: GCP project module with different versions - CONFLICT
module "gcp_project_app1" {
  source  = "terraform-google-modules/project-factory/google"
  version = "14.0.0"

  name = "app1-project"
}

module "gcp_project_app2" {
  source  = "terraform-google-modules/project-factory/google"
  version = "14.1.0"

  name = "app2-project"
}

# Scenario 4: Custom registry with different versions - CONFLICT
module "custom_module_a" {
  source  = "app.terraform.io/company/custom-module/aws"
  version = "1.2.3"

  config = "a"
}

module "custom_module_b" {
  source  = "app.terraform.io/company/custom-module/aws"
  version = "1.2.4"

  config = "b"
}

# Scenario 5: Same module, one with version, one without - CONFLICT
module "s3_bucket_with_version" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.0.0"

  bucket = "my-bucket-1"
}

module "s3_bucket_no_version" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket = "my-bucket-2"
}
