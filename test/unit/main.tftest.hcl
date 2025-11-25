# Terraform test file for unit tests
# Tests basic variable validation and output functionality

run "test_default_values" {
  command = plan

  assert {
    condition     = var.test_string == "hello"
    error_message = "Default string value should be 'hello'"
  }

  assert {
    condition     = var.test_number == 42
    error_message = "Default number value should be 42"
  }

  assert {
    condition     = length(var.test_list) == 2
    error_message = "Default list should have 2 items"
  }
}

run "test_custom_string" {
  command = plan

  variables {
    test_string = "world"
  }

  assert {
    condition     = var.test_string == "world"
    error_message = "Custom string value should be 'world'"
  }

  assert {
    condition     = output.test_string_output == "world"
    error_message = "Output should match input string"
  }
}

run "test_custom_number" {
  command = plan

  variables {
    test_number = 100
  }

  assert {
    condition     = var.test_number == 100
    error_message = "Custom number value should be 100"
  }

  assert {
    condition     = var.test_number > 0
    error_message = "Number should be positive"
  }
}

run "test_validation_positive_number" {
  command = plan

  variables {
    test_number = 1
  }

  assert {
    condition     = var.test_number > 0
    error_message = "Validation should pass for positive numbers"
  }
}

run "test_custom_list" {
  command = plan

  variables {
    test_list = ["a", "b", "c"]
  }

  assert {
    condition     = length(var.test_list) == 3
    error_message = "Custom list should have 3 items"
  }

  assert {
    condition     = contains(var.test_list, "a")
    error_message = "List should contain 'a'"
  }
}
