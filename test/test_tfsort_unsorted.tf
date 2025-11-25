# Test file with UNSORTED variables and outputs - should FAIL tfsort check

# Variables in WRONG order (should be alphabetically sorted)
variable "zebra_config" {
  description = "Zebra configuration"
  type        = string
  default     = "zebra"
}

variable "apple_config" {
  description = "Apple configuration"
  type        = string
  default     = "apple"
}

variable "monkey_config" {
  description = "Monkey configuration"
  type        = string
  default     = "monkey"
}

variable "banana_config" {
  description = "Banana configuration"
  type        = string
  default     = "banana"
}

# Outputs in WRONG order (should be alphabetically sorted)
output "zebra_output" {
  description = "Zebra output value"
  value       = var.zebra_config
}

output "apple_output" {
  description = "Apple output value"
  value       = var.apple_config
}

output "monkey_output" {
  description = "Monkey output value"
  value       = var.monkey_config
}

output "banana_output" {
  description = "Banana output value"
  value       = var.banana_config
}
