# Integration Test Example - Simulated resource creation
# These tests simulate more complex scenarios with resource interactions

terraform {
  required_version = ">= 1.5"
}

variable "environment" {
  type    = string
  default = "test"
}

variable "resource_count" {
  type    = number
  default = 3
}

# Simulated "null_resource" for testing (doesn't require provider configuration)
resource "terraform_data" "test_resources" {
  count = var.resource_count

  input = {
    name        = "resource-${count.index}"
    environment = var.environment
    index       = count.index
  }
}

# Simulated configuration data
locals {
  resource_names = [
    for i in range(var.resource_count) : "resource-${i}"
  ]

  resource_map = {
    for idx, res in terraform_data.test_resources :
    idx => res.input.name
  }
}

output "resource_names" {
  value       = local.resource_names
  description = "List of resource names"
}

output "resource_count" {
  value       = length(terraform_data.test_resources)
  description = "Number of resources created"
}

output "resource_map" {
  value       = local.resource_map
  description = "Map of resource indices to names"
}

output "environment" {
  value       = var.environment
  description = "Environment name"
}
