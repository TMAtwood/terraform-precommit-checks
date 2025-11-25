# Test file for GIT MODULE version conflicts
# Tests various git reference patterns

# Scenario 1: Same module, different commit hashes - CONFLICT
module "networking_primary" {
  source = "git::https://github.com/company/terraform-networking.git?commit=abc123456"

  vpc_cidr = "10.0.0.0/16"
}

module "networking_secondary" {
  source = "git::https://github.com/company/terraform-networking.git?commit=def789012"

  vpc_cidr = "10.1.0.0/16"
}

# Scenario 2: Same module with git protocol, different tags - CONFLICT
module "security_dev" {
  source = "git::git@github.com:company/terraform-security.git?tag=v1.0.0"

  environment = "dev"
}

module "security_prod" {
  source = "git::git@github.com:company/terraform-security.git?tag=v2.0.0"

  environment = "prod"
}

# Scenario 3: Same module with https protocol, different refs - CONFLICT
module "database_app1" {
  source = "git::https://gitlab.com/company/terraform-database.git?ref=release-1.0"

  db_name = "app1"
}

module "database_app2" {
  source = "git::https://gitlab.com/company/terraform-database.git?ref=release-2.0"

  db_name = "app2"
}

# Scenario 4: Git URL with subdirectory - different refs - CONFLICT
module "compute_east" {
  source = "git::https://github.com/company/terraform-modules.git//modules/compute?ref=v1.5.0"

  region = "us-east-1"
}

module "compute_west" {
  source = "git::https://github.com/company/terraform-modules.git//modules/compute?ref=v1.6.0"

  region = "us-west-2"
}
