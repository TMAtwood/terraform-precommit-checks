# Test case: Valid tags with pattern validation - should PASS
# Tags match required regex patterns

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Valid: CostCenter matches pattern CC-#### format
resource "aws_instance" "valid_cost_center" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  tags = {
    Environment = "Production"
    Owner       = "admin@example.com"
    CostCenter  = "CC-1234"  # Matches ^CC-[0-9]{4}$
    TicketID    = "JIRA-5678"  # Matches ^[A-Z]+-[0-9]+$
  }
}

# Valid: All patterns match
resource "aws_vpc" "valid_all_patterns" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Environment = "Development"
    Owner       = "team@company.com"  # Matches email pattern
    CostCenter  = "CC-9999"  # Matches ^CC-[0-9]{4}$
    TicketID    = "PROJ-12345"  # Matches ^[A-Z]+-[0-9]+$
  }
}

# Valid: Email format with complex pattern
resource "aws_s3_bucket" "valid_email" {
  bucket = "my-bucket"

  tags = {
    Environment = "Staging"
    Owner       = "john.doe+tags@sub.example.com"  # Complex email pattern
    CostCenter  = "CC-0001"
    TicketID    = "BUG-999"
  }
}

# Valid: Azure resource with patterns
resource "azurerm_resource_group" "valid_azure_patterns" {
  name     = "example-rg"
  location = "East US"

  tags = {
    Environment = "Production"
    Owner       = "azure-admin@company.com"
    CostCenter  = "CC-5555"
    TicketID    = "AZURE-1001"
  }
}

# Valid: Edge cases - minimum valid values
resource "aws_ebs_volume" "valid_edge_cases" {
  availability_zone = "us-west-2a"
  size              = 10

  tags = {
    Environment = "Development"
    Owner       = "a@b.co"  # Shortest valid email
    CostCenter  = "CC-0000"  # All zeros
    TicketID    = "A-0"  # Minimal ticket
  }
}
