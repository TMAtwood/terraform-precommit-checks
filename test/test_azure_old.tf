# Example: Azure (azurerm) provider - OLD STYLE
# This should be flagged by the pre-commit hook

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

# OLD PATTERN - This will be flagged!
provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "example" {
  name     = "my-resource-group"
  location = var.location
}

output "resource_group_id" {
  value = azurerm_resource_group.example.id
}
