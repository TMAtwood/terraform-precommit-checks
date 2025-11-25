# Unit Test Example - Simple variable validation tests
# These tests validate basic functionality without external dependencies

variable "test_string" {
  type    = string
  default = "hello"

  validation {
    condition     = length(var.test_string) > 0
    error_message = "String must not be empty"
  }
}

variable "test_number" {
  type    = number
  default = 42

  validation {
    condition     = var.test_number > 0
    error_message = "Number must be positive"
  }
}

variable "test_list" {
  type    = list(string)
  default = ["item1", "item2"]

  validation {
    condition     = length(var.test_list) > 0
    error_message = "List must not be empty"
  }
}

output "test_string_output" {
  value = var.test_string
}

output "test_number_output" {
  value = var.test_number
}

output "test_list_output" {
  value = var.test_list
}
