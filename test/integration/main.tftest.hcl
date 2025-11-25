# Integration tests for resource creation and interaction
# These tests validate resource behavior and outputs

run "test_default_resource_creation" {
  command = plan

  assert {
    condition     = length(terraform_data.test_resources) == 3
    error_message = "Should create 3 resources by default"
  }

  assert {
    condition     = var.environment == "test"
    error_message = "Default environment should be 'test'"
  }
}

run "test_resource_outputs" {
  command = plan

  assert {
    condition     = length(output.resource_names) == 3
    error_message = "Should output 3 resource names"
  }

  assert {
    condition     = output.resource_count == 3
    error_message = "Resource count output should be 3"
  }

  assert {
    condition     = output.environment == "test"
    error_message = "Environment output should be 'test'"
  }
}

run "test_custom_resource_count" {
  command = plan

  variables {
    resource_count = 5
  }

  assert {
    condition     = length(terraform_data.test_resources) == 5
    error_message = "Should create 5 resources when specified"
  }

  assert {
    condition     = output.resource_count == 5
    error_message = "Resource count output should match variable"
  }
}

run "test_custom_environment" {
  command = plan

  variables {
    environment = "production"
  }

  assert {
    condition     = var.environment == "production"
    error_message = "Environment should be 'production'"
  }

  assert {
    condition     = output.environment == "production"
    error_message = "Environment output should match input"
  }
}

run "test_resource_naming" {
  command = plan

  assert {
    condition     = contains(output.resource_names, "resource-0")
    error_message = "Should contain resource-0"
  }

  assert {
    condition     = contains(output.resource_names, "resource-1")
    error_message = "Should contain resource-1"
  }

  assert {
    condition     = contains(output.resource_names, "resource-2")
    error_message = "Should contain resource-2"
  }
}

run "test_resource_map_structure" {
  command = plan

  assert {
    condition     = length(output.resource_map) == 3
    error_message = "Resource map should have 3 entries"
  }

  assert {
    condition     = output.resource_map[0] == "resource-0"
    error_message = "First resource should be named resource-0"
  }
}

run "test_single_resource" {
  command = plan

  variables {
    resource_count = 1
    environment    = "dev"
  }

  assert {
    condition     = output.resource_count == 1
    error_message = "Should create single resource"
  }

  assert {
    condition     = output.environment == "dev"
    error_message = "Environment should be 'dev'"
  }
}
