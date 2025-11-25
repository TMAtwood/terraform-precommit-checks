# Test file with PROPERLY SORTED variables - should PASS tfsort check

variable "apple_config" {
  description = "Apple configuration"
  type        = string
  default     = "apple"
}

variable "banana_config" {
  description = "Banana configuration"
  type        = string
  default     = "banana"
}

variable "monkey_config" {
  description = "Monkey configuration"
  type        = string
  default     = "monkey"
}

variable "zebra_config" {
  description = "Zebra configuration"
  type        = string
  default     = "zebra"
}
