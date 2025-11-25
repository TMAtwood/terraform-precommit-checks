# Example: AWS provider - NEW STYLE (CORRECT)
# This should pass the pre-commit hook

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.0"
      configuration_aliases = [aws.main]
    }
  }
}

variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
}

# Resources use the aliased provider
resource "aws_s3_bucket" "example" {
  provider = aws.main
  bucket   = var.bucket_name

  tags = {
    Environment = "dev"
    Purpose     = "example"
  }
}

output "bucket_arn" {
  description = "The ARN of the S3 bucket"
  value       = aws_s3_bucket.example.arn
}
