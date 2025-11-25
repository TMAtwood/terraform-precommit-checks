# Test file with MIXED module sources - should PASS
# Different modules from different sources, no conflicts

# Registry module - AWS VPC (consistent version)
module "vpc_prod" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "prod-vpc"
  cidr = "10.0.0.0/16"
}

module "vpc_dr" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "dr-vpc"
  cidr = "10.10.0.0/16"
}

# Different registry module - AWS EKS (different module, no conflict)
module "eks_cluster" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.0.0"

  cluster_name = "main-cluster"
}

# Git module with consistent ref
module "custom_networking_east" {
  source = "git::https://github.com/company/terraform-networking.git?ref=v2.0.0"

  region = "us-east-1"
}

module "custom_networking_west" {
  source = "git::https://github.com/company/terraform-networking.git?ref=v2.0.0"

  region = "us-west-2"
}

# Different git module (different repo, no conflict)
module "security_config" {
  source = "git::https://github.com/company/terraform-security.git?ref=v1.0.0"

  environment = "production"
}

# Local modules (should be ignored by checker)
module "local_helper" {
  source = "./modules/helper"

  config = "value1"
}

module "local_helper_2" {
  source = "./modules/helper"

  config = "value2"
}

module "parent_local" {
  source = "../shared-modules/compute"

  instance_type = "t3.micro"
}

# Azure module (different from AWS, no conflict)
module "azure_vnet" {
  source  = "Azure/network/azurerm"
  version = "5.0.0"

  resource_group_name = "rg-main"
}

# GCP module (different from others, no conflict)
module "gcp_network" {
  source  = "terraform-google-modules/network/google"
  version = "7.0.0"

  project_id = "my-project"
}
