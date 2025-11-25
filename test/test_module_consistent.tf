# Test file demonstrating CONSISTENT module versions
# This should PASS the check-module-versions hook

# Reference 1: Using version 3.0.0
module "vpc_dev" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"

  name = "dev-vpc"
  cidr = "10.0.0.0/16"
}

# Reference 2: Using same version 3.0.0 - CONSISTENT!
module "vpc_prod" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"

  name = "prod-vpc"
  cidr = "10.1.0.0/16"
}

# Reference 3: Different module entirely (no conflict)
module "s3_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "2.0.0"

  bucket = "my-app-bucket"
}

# Reference 4: Git module with consistent ref
module "security_group_app" {
  source = "git::https://github.com/example/terraform-security-groups.git?ref=v1.5.0"

  name = "app-sg"
}

# Reference 5: Same git module with same ref - CONSISTENT!
module "security_group_db" {
  source = "git::https://github.com/example/terraform-security-groups.git?ref=v1.5.0"

  name = "db-sg"
}

# Local modules are ignored (no version checking needed)
module "local_helper" {
  source = "./modules/helper"

  config = "value"
}

module "local_helper_2" {
  source = "./modules/helper"

  config = "other-value"
}
