# Test case: Invalid tags with pattern validation - should FAIL
# Tags do not match required regex patterns

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Invalid: CostCenter doesn't match pattern (missing CC- prefix)
resource "aws_instance" "invalid_cost_center_format" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  tags = {
    Environment = "Production"
    Owner       = "admin@example.com"
    CostCenter  = "1234"  # Should be CC-1234
    TicketID    = "JIRA-5678"
  }
}

# Invalid: CostCenter has wrong number of digits
resource "aws_vpc" "invalid_cost_center_digits" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Environment = "Development"
    Owner       = "team@company.com"
    CostCenter  = "CC-123"  # Should be 4 digits, not 3
    TicketID    = "PROJ-12345"
  }
}

# Invalid: TicketID doesn't match pattern (lowercase letters)
resource "aws_s3_bucket" "invalid_ticket_format" {
  bucket = "my-bucket"

  tags = {
    Environment = "Staging"
    Owner       = "admin@example.com"
    CostCenter  = "CC-1234"
    TicketID    = "jira-5678"  # Should be uppercase: JIRA-5678
  }
}

# Invalid: Owner email format is wrong (no @ symbol)
resource "aws_subnet" "invalid_email_format" {
  vpc_id     = "vpc-12345"
  cidr_block = "10.0.1.0/24"

  tags = {
    Environment = "Production"
    Owner       = "admin.example.com"  # Missing @ symbol
    CostCenter  = "CC-1234"
    TicketID    = "INFRA-100"
  }
}

# Invalid: Multiple pattern violations
resource "aws_security_group" "multiple_pattern_violations" {
  name        = "test-sg"
  description = "Test security group"

  tags = {
    Environment = "Production"
    Owner       = "notanemail"  # Not an email
    CostCenter  = "COST-1234"  # Wrong prefix (COST instead of CC)
    TicketID    = "12345"  # Missing project prefix
  }
}

# Invalid: CostCenter with special characters
resource "aws_lb" "invalid_special_chars" {
  name               = "test-lb"
  load_balancer_type = "application"

  tags = {
    Environment = "Development"
    Owner       = "admin@example.com"
    CostCenter  = "CC-12@4"  # Has @ symbol instead of digit
    TicketID    = "PROJ-5678"
  }
}

# Invalid: TicketID missing number after dash
resource "azurerm_virtual_network" "invalid_ticket_no_number" {
  name                = "test-vnet"
  resource_group_name = "test-rg"
  address_space       = ["10.0.0.0/16"]
  location            = "East US"

  tags = {
    Environment = "Production"
    Owner       = "azure@example.com"
    CostCenter  = "CC-9999"
    TicketID    = "AZURE-"  # Missing number after dash
  }
}

# Invalid: Owner email with spaces (not allowed)
resource "aws_db_instance" "invalid_email_spaces" {
  identifier           = "test-db"
  engine               = "postgres"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  username             = "admin"
  password             = "password123"  # pragma: allowlist secret
  skip_final_snapshot  = true

  tags = {
    Environment = "Production"
    Owner       = "admin user@example.com"  # Space in email
    CostCenter  = "CC-1234"
    TicketID    = "DB-100"
  }
}
