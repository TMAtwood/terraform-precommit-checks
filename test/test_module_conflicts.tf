# Test file demonstrating MODULE VERSION CONFLICTS
# This should FAIL the check-module-versions hook

# Reference 1: Using version 1.0.0
module "vpc_dev" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "1.0.0"

  name = "dev-vpc"
  cidr = "10.0.0.0/16"
}

# Reference 2: Using version 2.0.0 - CONFLICT!
module "vpc_prod" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "2.0.0"

  name = "prod-vpc"
  cidr = "10.1.0.0/16"
}

# Reference 3: Git module with ref=v1.0.0
module "security_group_app" {
  source = "git::https://github.com/example/terraform-security-groups.git?ref=v1.0.0"

  name = "app-sg"
}

# Reference 4: Same git module with different ref - CONFLICT!
module "security_group_db" {
  source = "git::https://github.com/example/terraform-security-groups.git?ref=v2.0.0"

  name = "db-sg"
}

# Reference 5: Git module with commit hash
module "iam_roles_admin" {
  source = "git::https://github.com/example/terraform-iam.git?commit=abc123def456"

  role_name = "admin"
}

# Reference 6: Same git module with different commit - CONFLICT!
module "iam_roles_readonly" {
  source = "git::https://github.com/example/terraform-iam.git?commit=xyz789abc012"

  role_name = "readonly"
}
