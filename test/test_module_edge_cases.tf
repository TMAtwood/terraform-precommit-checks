# Test file for EDGE CASES - should PASS
# Tests unusual but valid module reference patterns

# Module with no version specified (but only one reference - OK)
module "unique_module" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "my-function"
}

# Git module with branch reference (only one reference - OK)
module "feature_branch" {
  source = "git::https://github.com/company/terraform-feature.git?ref=feature/new-capability"

  enabled = true
}

# Bitbucket git module
module "bitbucket_module" {
  source = "git::https://bitbucket.org/company/terraform-modules.git?ref=v1.0.0"

  config = "value"
}

# Generic git protocol
module "generic_git" {
  source = "git::git@gitlab.company.com:infrastructure/modules.git?tag=release-1.0"

  environment = "production"
}

# Module with multiple query parameters
module "complex_git_url" {
  source = "git::https://github.com/company/modules.git//subdir?ref=v1.0.0&depth=1"

  name = "complex"
}

# HTTP module source (not common but valid)
module "http_module" {
  source = "https://example.com/terraform-modules/module.zip"

  config = "value"
}

# Private registry with custom hostname
module "private_registry" {
  source  = "registry.company.com/team/module/provider"
  version = "2.0.0"

  setting = "value"
}

# Module with very long version constraint
module "complex_version" {
  source  = "terraform-aws-modules/rds/aws"
  version = ">= 5.0.0, < 6.0.0"

  identifier = "mydb"
}

# GitHub with SSH (single reference)
module "ssh_github" {
  source = "git::ssh://git@github.com/company/modules.git?ref=main"

  config = "ssh"
}

# Terraform Cloud/Enterprise registry
module "tfe_module" {
  source  = "app.terraform.io/organization/module/provider"
  version = "1.0.0"

  name = "tfe-resource"
}
