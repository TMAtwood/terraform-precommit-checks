#!/usr/bin/env python3
"""
Pre-commit hook to detect old-style provider configurations in Terraform/OpenTofu modules.

Old pattern (blocks module-level for_each and depends_on):
    provider "aws" {
      region = var.region
    }

New pattern (required):
    terraform {
      required_providers {
        aws = {
          source  = "hashicorp/aws"
          version = "~> 5.0"
        }
      }
    }

    # Provider configuration should use configuration_aliases
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


class ProviderConfigChecker:
    """Check for old-style provider configurations in Terraform/OpenTofu files."""

    # Pattern to detect provider blocks outside of required_providers
    PROVIDER_BLOCK_PATTERN = re.compile(r'^\s*provider\s+"([^"]+)"\s*\{', re.MULTILINE)

    # Pattern to detect required_providers block
    REQUIRED_PROVIDERS_PATTERN = re.compile(
        r"terraform\s*\{[^}]*required_providers\s*\{", re.MULTILINE | re.DOTALL
    )

    # Pattern to check if we're in a module (not root)
    MODULE_INDICATORS = ["variables.tf", "outputs.tf"]

    def __init__(self, files: List[str]):
        self.files = files
        self.errors: List[Tuple[str, int, str]] = []

    def is_module_directory(self, file_path: Path) -> bool:
        """Determine if a file is part of a module (not root)."""
        directory = file_path.parent

        # Check if directory contains typical module files
        for indicator in self.MODULE_INDICATORS:
            if (directory / indicator).exists():
                return True

        # Check if this is in a 'modules' subdirectory
        return "modules" in directory.parts

    def check_file(self, file_path: str) -> bool:
        """
        Check a single file for old-style provider configurations.

        Returns:
            True if file passes checks, False if errors found
        """
        path = Path(file_path)

        # Only check .tf files
        if path.suffix != ".tf":
            return True

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return False

        # Find all provider blocks
        provider_matches = list(self.PROVIDER_BLOCK_PATTERN.finditer(content))

        if not provider_matches:
            return True

        for match in provider_matches:
            provider_name = match.group(1)

            # Find the line number
            line_num = content[: match.start()].count("\n") + 1

            # Check if this is inside a required_providers or mock_provider block
            # (some testing frameworks use mock providers)
            start_pos = match.start()
            context_start = max(0, start_pos - 500)
            context = content[context_start:start_pos]

            # Skip if inside required_providers or configuration_aliases
            if "required_providers" in context or "configuration_aliases" in context:
                continue

            # Skip if this is a mock or test provider
            if "mock_provider" in context or "# test" in context.lower():
                continue

            # This is an old-style provider block
            is_module = self.is_module_directory(path)

            error_msg = (
                f"Old-style provider configuration detected for '{provider_name}'. "
                f"This prevents module-level for_each and depends_on."
            )

            if is_module:
                error_msg += (
                    "\n  → Modules should use required_providers with "
                    "configuration_aliases instead."
                    "\n  → See: https://developer.hashicorp.com/terraform/"
                    "language/modules/develop/providers"
                )
            else:
                error_msg += (
                    "\n  → Root modules should declare providers in required_providers block."
                )

            self.errors.append((file_path, line_num, error_msg))

        return len(self.errors) == 0

    def check_all_files(self) -> bool:
        """
        Check all files provided to the checker.

        Returns:
            True if all files pass, False otherwise
        """
        all_passed = True

        for file_path in self.files:
            if not self.check_file(file_path):
                all_passed = False

        return all_passed

    def print_errors(self) -> None:
        """Print all errors found during checking."""
        if not self.errors:
            return

        print("\n" + "=" * 80, file=sys.stderr)
        print("❌ OLD-STYLE PROVIDER CONFIGURATION DETECTED", file=sys.stderr)
        print("=" * 80, file=sys.stderr)

        for file_path, line_num, error_msg in self.errors:
            print(f"\n📁 File: {file_path}", file=sys.stderr)
            print(f"📍 Line: {line_num}", file=sys.stderr)
            print(f"⚠️  {error_msg}", file=sys.stderr)

        print("\n" + "=" * 80, file=sys.stderr)
        print("💡 RECOMMENDED FIX:", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        print(
            """
For modules, use required_providers with configuration_aliases:

    terraform {
      required_providers {
        <provider> = {
          source                = "<source>"
          version               = "<version>"
          configuration_aliases = [<provider>.main]
        }
      }
    }

Then reference providers when calling the module:

    module "example" {
      source = "./modules/my-module"

      providers = {
        <provider>.main = <provider>.alias_name
      }

      # Now for_each and depends_on work!
      for_each   = var.instances
      depends_on = [<resource>]
    }

Examples for common providers:
  • AWS (aws):        source = "hashicorp/aws"
  • Azure (azurerm):  source = "hashicorp/azurerm"
  • GCP (google):     source = "hashicorp/google"
  • Oracle (oci):     source = "oracle/oci"
""",
            file=sys.stderr,
        )
        print("=" * 80 + "\n", file=sys.stderr)


def main() -> int:
    """Main entry point for the pre-commit hook."""
    parser = argparse.ArgumentParser(
        description="Check for old-style provider configurations in Terraform/OpenTofu files"
    )
    parser.add_argument("files", nargs="*", help="Files to check")

    args = parser.parse_args()

    if not args.files:
        print("No files to check", file=sys.stderr)
        return 0

    checker = ProviderConfigChecker(args.files)

    if checker.check_all_files():
        print("✅ All provider configurations are using the new pattern", file=sys.stderr)
        return 0
    else:
        checker.print_errors()
        return 1


if __name__ == "__main__":
    sys.exit(main())
