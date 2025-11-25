# Test case: Invalid tags - should FAIL
# Various tag validation errors

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Invalid: Missing required tag (CostCenter)
resource "aws_instance" "missing_required_tag" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"

  tags = {
    Environment = "Production"
    Owner       = "john.doe@example.com"
  }
}

# Invalid: Tag key has wrong case (environment vs Environment)
resource "aws_vpc" "wrong_case_tag_key" {
  cidr_block = "10.0.0.0/16"

  tags = {
    environment = "Production"  # Should be "Environment"
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
  }
}

# Invalid: Tag value has wrong case (production vs Production)
resource "aws_subnet" "wrong_case_tag_value" {
  vpc_id     = aws_vpc.wrong_case_tag_key.id
  cidr_block = "10.0.1.0/24"

  tags = {
    Environment = "production"  # Should be "Production", "Development", or "Staging"
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
  }
}

# Invalid: Tag has empty value
resource "aws_security_group" "empty_tag_value" {
  name        = "test-sg"
  description = "Test security group"
  vpc_id      = aws_vpc.wrong_case_tag_key.id

  tags = {
    Environment = "Production"
    Owner       = ""  # Empty value
    CostCenter  = "CC-1234"
  }
}

# Invalid: Tag value not in allowed list
resource "aws_lb" "invalid_tag_value" {
  name               = "test-lb"
  load_balancer_type = "application"

  tags = {
    Environment = "Testing"  # Not in allowed values list
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
  }
}

# Invalid: Multiple issues - missing tags, wrong case, invalid value
resource "aws_db_instance" "multiple_issues" {
  identifier           = "test-db"
  engine               = "postgres"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  username             = "admin"
  password             = "password123"  # pragma: allowlist secret
  skip_final_snapshot  = true

  tags = {
    environment = "prod"  # Wrong case key AND invalid value
    owner       = "team@example.com"  # Wrong case key
    # Missing CostCenter
  }
}

# Invalid: Optional tag with wrong case
resource "aws_ebs_volume" "optional_tag_wrong_case" {
  availability_zone = "us-west-2a"
  size              = 10

  tags = {
    Environment = "Production"
    Owner       = "team@example.com"
    CostCenter  = "CC-1234"
    project     = "MyProject"  # Should be "Project" (capital P)
  }
}

# Invalid: No tags block on taggable resource
resource "aws_s3_bucket" "no_tags" {
  bucket = "my-test-bucket"
}

# Invalid: Azure resource with missing required tags
resource "azurerm_linux_virtual_machine" "azure_missing_tags" {
  name                = "test-vm"
  resource_group_name = "test-rg"
  location            = "East US"
  size                = "Standard_B1s"
  admin_username      = "adminuser"

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  # Missing tags entirely
}
