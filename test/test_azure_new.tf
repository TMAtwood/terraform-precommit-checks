# Example: Azure (azurerm) provider - NEW STYLE (CORRECT)
# This should pass the pre-commit hook

terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source                = "hashicorp/azurerm"
      version               = "~> 3.0"
      configuration_aliases = [azurerm.main]
    }
  }
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

# Resources use the aliased provider
resource "azurerm_resource_group" "example" {
  provider = azurerm.main
  name     = "my-resource-group"
  location = var.location

  tags = {
    Environment = "dev"
    Purpose     = "example"
  }
}

output "resource_group_id" {
  description = "The ID of the resource group"
  value       = azurerm_resource_group.example.id
}
