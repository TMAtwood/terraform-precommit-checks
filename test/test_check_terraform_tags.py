"""
Pytest tests for check_terraform_tags.py hook.

Tests tag validation including:
- Required tags with allowed values
- Required tags with pattern validation
- Optional tags with case sensitivity
- Multi-provider support (AWS, Azure, GCP)
"""

import sys
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from check_terraform_tags import TerraformTagChecker


class TestBasicTagValidation:
    """Test basic tag validation functionality."""

    def test_valid_tags_all_present(self, tmp_path):
        """Test that resources with all required tags pass validation."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Environment = "Development"
    Owner       = "admin@example.com"
    CostCenter  = "CC-1234"
  }
}
"""
        )

        required_tags = [
            {"name": "Environment", "allowed_values": ["Development", "Staging", "Production"]},
            {"name": "Owner"},
            {"name": "CostCenter"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is True
        assert len(checker.errors) == 0

    def test_missing_required_tag(self, tmp_path):
        """Test that missing required tags are detected."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Environment = "Development"
    Owner       = "admin@example.com"
  }
}
"""
        )

        required_tags = [
            {"name": "Environment"},
            {"name": "Owner"},
            {"name": "CostCenter"},  # Missing
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is False
        assert len(checker.errors) == 1
        assert "CostCenter" in checker.errors[0][3]
        assert "missing" in checker.errors[0][3].lower()

    def test_wrong_case_tag_key(self, tmp_path):
        """Test that incorrect case in tag keys is detected."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    environment = "Development"  # Should be "Environment"
    Owner       = "admin@example.com"
    CostCenter  = "CC-1234"
  }
}
"""
        )

        required_tags = [
            {"name": "Environment"},
            {"name": "Owner"},
            {"name": "CostCenter"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is False
        assert len(checker.errors) == 1
        assert "Environment" in checker.errors[0][3]
        assert "incorrect case" in checker.errors[0][3].lower()

    def test_empty_tag_value(self, tmp_path):
        """Test that empty tag values are detected."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Environment = "Development"
    Owner       = ""  # Empty value
    CostCenter  = "CC-1234"
  }
}
"""
        )

        required_tags = [
            {"name": "Environment"},
            {"name": "Owner"},
            {"name": "CostCenter"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is False
        assert len(checker.errors) == 1
        assert "Owner" in checker.errors[0][3]
        assert "empty" in checker.errors[0][3].lower()


class TestAllowedValues:
    """Test allowed values validation."""

    def test_valid_allowed_value(self, tmp_path):
        """Test that valid allowed values pass validation."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Environment = "Production"
  }
}
"""
        )

        required_tags = [
            {"name": "Environment", "allowed_values": ["Development", "Staging", "Production"]},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is True

    def test_invalid_allowed_value(self, tmp_path):
        """Test that invalid allowed values are detected."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Environment = "Testing"  # Not in allowed values
  }
}
"""
        )

        required_tags = [
            {"name": "Environment", "allowed_values": ["Development", "Staging", "Production"]},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is False
        assert len(checker.errors) == 1
        assert "invalid value" in checker.errors[0][3].lower()

    def test_wrong_case_allowed_value(self, tmp_path):
        """Test that incorrect case in allowed values is detected."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Environment = "production"  # Should be "Production"
  }
}
"""
        )

        required_tags = [
            {"name": "Environment", "allowed_values": ["Development", "Staging", "Production"]},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is False
        assert "incorrect case" in checker.errors[0][3].lower()


class TestPatternValidation:
    """Test regex pattern validation."""

    def test_valid_email_pattern(self, tmp_path):
        """Test that valid email pattern passes validation."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Owner = "admin@example.com"
  }
}
"""
        )

        required_tags = [
            {"name": "Owner", "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is True

    def test_invalid_email_pattern(self, tmp_path):
        """Test that invalid email pattern is detected."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Owner = "admin"  # Not an email
  }
}
"""
        )

        required_tags = [
            {"name": "Owner", "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is False
        assert len(checker.errors) == 1
        assert "does not match required pattern" in checker.errors[0][3]

    def test_valid_cost_center_pattern(self, tmp_path):
        """Test that valid cost center pattern passes validation."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    CostCenter = "CC-1234"
  }
}
"""
        )

        required_tags = [
            {"name": "CostCenter", "pattern": r"^CC-[0-9]{4}$"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is True

    def test_invalid_cost_center_pattern(self, tmp_path):
        """Test that invalid cost center pattern is detected."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    CostCenter = "1234"  # Missing CC- prefix
  }
}
"""
        )

        required_tags = [
            {"name": "CostCenter", "pattern": r"^CC-[0-9]{4}$"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is False
        assert "does not match required pattern" in checker.errors[0][3]

    def test_valid_ticket_id_pattern(self, tmp_path):
        """Test that valid ticket ID pattern passes validation."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    TicketID = "JIRA-5678"
  }
}
"""
        )

        required_tags = [
            {"name": "TicketID", "pattern": r"^[A-Z]+-[0-9]+$"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is True

    def test_invalid_ticket_id_pattern_lowercase(self, tmp_path):
        """Test that lowercase ticket ID is detected."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    TicketID = "jira-5678"  # Should be uppercase
  }
}
"""
        )

        required_tags = [
            {"name": "TicketID", "pattern": r"^[A-Z]+-[0-9]+$"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is False
        assert "does not match required pattern" in checker.errors[0][3]

    def test_multiple_patterns(self, tmp_path):
        """Test multiple pattern validations in one resource."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Owner      = "admin@example.com"
    CostCenter = "CC-1234"
    TicketID   = "PROJ-999"
  }
}
"""
        )

        required_tags = [
            {"name": "Owner", "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
            {"name": "CostCenter", "pattern": r"^CC-[0-9]{4}$"},
            {"name": "TicketID", "pattern": r"^[A-Z]+-[0-9]+$"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is True


class TestOptionalTags:
    """Test optional tag validation."""

    def test_optional_tag_correct_case(self, tmp_path):
        """Test that optional tags with correct case pass validation."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Environment = "Development"
    Project     = "MyProject"
  }
}
"""
        )

        required_tags = [{"name": "Environment"}]
        optional_tags = [{"name": "Project"}]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
            optional_tags=optional_tags,
        )

        assert checker.check_all_files() is True

    def test_optional_tag_missing_ok(self, tmp_path):
        """Test that missing optional tags are acceptable."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Environment = "Development"
  }
}
"""
        )

        required_tags = [{"name": "Environment"}]
        optional_tags = [{"name": "Project"}]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
            optional_tags=optional_tags,
        )

        assert checker.check_all_files() is True

    def test_optional_tag_wrong_case(self, tmp_path):
        """Test that optional tags with wrong case are detected."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Environment = "Development"
    project     = "MyProject"  # Should be "Project"
  }
}
"""
        )

        required_tags = [{"name": "Environment"}]
        optional_tags = [{"name": "Project"}]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
            optional_tags=optional_tags,
        )

        assert checker.check_all_files() is False
        assert "incorrect case" in checker.errors[0][3].lower()


class TestMultiProvider:
    """Test multi-provider support."""

    def test_azure_tags(self, tmp_path):
        """Test Azure resource tag validation."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "azurerm_resource_group" "test" {
  name     = "test-rg"
  location = "East US"

  tags = {
    Environment = "Production"
    Owner       = "azure@example.com"
  }
}
"""
        )

        required_tags = [
            {"name": "Environment"},
            {"name": "Owner"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is True

    def test_gcp_labels(self, tmp_path):
        """Test GCP resource labels validation (uses 'labels' not 'tags')."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "google_compute_instance" "test" {
  name         = "test-instance"
  machine_type = "n1-standard-1"

  labels = {
    Environment = "Development"
    Owner       = "gcp@example.com"
  }
}
"""
        )

        required_tags = [
            {"name": "Environment"},
            {"name": "Owner"},
        ]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        assert checker.check_all_files() is True


class TestDynamicTags:
    """Test that dynamic tags are skipped."""

    def test_tags_with_merge(self, tmp_path):
        """Test that tags using merge() are skipped."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = merge(var.common_tags, {
    Name = "test-instance"
  })
}
"""
        )

        required_tags = [{"name": "Environment"}]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        # Should pass because dynamic tags are skipped
        assert checker.check_all_files() is True

    def test_tags_from_variable(self, tmp_path):
        """Test that tags from variables are skipped."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = var.instance_tags
}
"""
        )

        required_tags = [{"name": "Environment"}]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        # Should pass because dynamic tags are skipped
        assert checker.check_all_files() is True


class TestNonTaggableResources:
    """Test that non-taggable resources are skipped."""

    def test_non_taggable_resource(self, tmp_path):
        """Test that non-taggable resources don't trigger validation."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_iam_policy_document" "test" {
  statement {
    effect = "Allow"
    actions = ["s3:GetObject"]
    resources = ["*"]
  }
}
"""
        )

        required_tags = [{"name": "Environment"}]

        checker = TerraformTagChecker(
            files=[str(tf_file)],
            required_tags=required_tags,
        )

        # Should pass because resource is not taggable
        assert checker.check_all_files() is True
