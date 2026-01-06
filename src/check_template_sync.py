#!/usr/bin/env python3
"""
Pre-commit hook to validate that repository scaffold files match a reference template.

This hook ensures that support files (like .editorconfig, .gitignore, .pre-commit-config.yaml,
Jenkinsfile, .terraform-tags.yaml, etc.) are present and up-to-date by comparing them against
a reference template directory using SHA256 hash comparison.

Usage:
    python check_template_sync.py --template-path /path/to/template [files...]

Example:
    python check_template_sync.py --template-path ~/templates/opentofu-module .
"""

import argparse
import hashlib
import sys
from pathlib import Path


class TemplateSyncChecker:
    """Check that repository scaffold files match a reference template."""

    # Directories to exclude from template sync checking
    EXCLUDED_DIRS = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".terraform",
        ".venv",
        "venv",
        "htmlcov",
        ".coverage",
        "dist",
        "build",
        "*.egg-info",
    }

    # Files to exclude from template sync checking
    EXCLUDED_FILES = {
        ".DS_Store",
        "Thumbs.db",
        ".terraform.lock.hcl",
        "terraform.tfstate",
        "terraform.tfstate.backup",
        "*.tfvars",
    }

    def __init__(self, template_path: str, repo_root: str = "."):
        """
        Initialize the template sync checker.

        Args:
            template_path: Path to the template directory containing reference files
            repo_root: Path to the repository root (default: current directory)
        """
        self.template_path = Path(template_path).resolve()
        self.repo_root = Path(repo_root).resolve()
        self.errors: list[str] = []
        self.warnings: list[str] = []

        # Validate template path exists
        if not self.template_path.exists():
            raise ValueError(f"Template path does not exist: {template_path}")
        if not self.template_path.is_dir():
            raise ValueError(f"Template path is not a directory: {template_path}")

    def should_exclude(self, path: Path, is_dir: bool = False) -> bool:
        """
        Check if a path should be excluded from template sync checking.

        Args:
            path: Path to check
            is_dir: Whether the path is a directory

        Returns:
            True if path should be excluded, False otherwise
        """
        name = path.name

        if is_dir:
            return name in self.EXCLUDED_DIRS

        # Check excluded files (exact match or pattern)
        if name in self.EXCLUDED_FILES:
            return True

        # Check patterns (e.g., *.tfvars)
        for pattern in self.EXCLUDED_FILES:
            if "*" in pattern:
                suffix = pattern.replace("*", "")
                if name.endswith(suffix):
                    return True

        return False

    def calculate_sha256(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hexadecimal SHA256 hash string
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files efficiently
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            raise RuntimeError(f"Failed to calculate hash for {file_path}: {e}") from e

    def get_template_structure(self) -> tuple[set[Path], dict[Path, str]]:
        """
        Walk the template directory and build a structure of directories and files.

        Returns:
            Tuple of (set of relative directory paths, dict of relative file paths to SHA256 hashes)
        """
        template_dirs: set[Path] = set()
        template_files: dict[Path, str] = {}

        for item in self.template_path.rglob("*"):
            # Skip excluded items
            if self.should_exclude(item, item.is_dir()):
                continue

            # Get relative path from template root
            try:
                rel_path = item.relative_to(self.template_path)
            except ValueError:
                continue

            # Skip if any parent directory is excluded
            should_skip = False
            for parent in rel_path.parents:
                if parent != Path(".") and self.should_exclude(
                    self.template_path / parent, is_dir=True
                ):
                    should_skip = True
                    break

            if should_skip:
                continue

            if item.is_dir():
                template_dirs.add(rel_path)
            elif item.is_file():
                # Calculate hash for template file
                try:
                    file_hash = self.calculate_sha256(item)
                    template_files[rel_path] = file_hash
                except Exception as e:
                    self.warnings.append(
                        f"⚠️  Could not calculate hash for template file: {rel_path}\n   Reason: {e}"
                    )

        return template_dirs, template_files

    def check_directories(self, template_dirs: set[Path]) -> None:
        """
        Check that all directories in the template exist in the repository.

        Args:
            template_dirs: Set of relative directory paths from template
        """
        for dir_path in sorted(template_dirs):
            repo_dir = self.repo_root / dir_path

            if not repo_dir.exists():
                self.errors.append(
                    f"📁 Missing directory: {dir_path}\n"
                    f"   Expected location: {repo_dir}\n"
                    f"   → This directory exists in the template but not in the repository.\n"
                    f"   → Create this directory to match the template structure."
                )
            elif not repo_dir.is_dir():
                self.errors.append(
                    f"📁 Path exists but is not a directory: {dir_path}\n"
                    f"   Location: {repo_dir}\n"
                    f"   → This path should be a directory according to the template.\n"
                    f"   → Remove the file and create a directory instead."
                )

    def check_files(self, template_files: dict[Path, str]) -> None:
        """
        Check that all files in the template exist in the repository with matching content.

        Args:
            template_files: Dict mapping relative file paths to their SHA256 hashes
        """
        for file_path, template_hash in sorted(template_files.items()):
            repo_file = self.repo_root / file_path
            template_file = self.template_path / file_path

            # Check if file exists
            if not repo_file.exists():
                self.errors.append(
                    f"📄 Missing file: {file_path}\n"
                    f"   Expected location: {repo_file}\n"
                    f"   Template location: {template_file}\n"
                    f"   → This file exists in the template but not in the repository.\n"
                    f"   → Copy this file from the template to maintain consistency."
                )
                continue

            # Check if it's actually a file
            if not repo_file.is_file():
                self.errors.append(
                    f"📄 Path exists but is not a file: {file_path}\n"
                    f"   Location: {repo_file}\n"
                    f"   → This path should be a file according to the template.\n"
                    f"   → Remove the directory and create a file instead."
                )
                continue

            # Calculate hash for repo file and compare
            try:
                repo_hash = self.calculate_sha256(repo_file)

                if repo_hash != template_hash:
                    self.errors.append(
                        f"📄 File content mismatch: {file_path}\n"
                        f"   Repository file: {repo_file}\n"
                        f"   Template file:   {template_file}\n"
                        f"   Repository SHA256: {repo_hash}\n"
                        f"   Template SHA256:   {template_hash}\n"
                        f"   → The file exists but has different content than the template.\n"
                        f"   → Update this file to match the template version.\n"
                        f"   → This ensures consistency and includes the latest best practices."
                    )
            except Exception as e:
                self.errors.append(
                    f"📄 Could not verify file: {file_path}\n"
                    f"   Location: {repo_file}\n"
                    f"   Reason: {e}\n"
                    f"   → Unable to calculate hash for comparison."
                )

    def check_sync(self) -> bool:
        """
        Check that repository matches the template structure and content.

        Returns:
            True if repository matches template, False otherwise
        """
        # Get template structure
        try:
            template_dirs, template_files = self.get_template_structure()
        except Exception as e:
            self.errors.append(
                f"❌ Failed to read template structure: {e}\n   Template path: {self.template_path}"
            )
            return False

        # Check directories
        self.check_directories(template_dirs)

        # Check files
        self.check_files(template_files)

        return len(self.errors) == 0

    def print_results(self) -> None:
        """Print check results including errors and warnings."""
        # Print warnings first (non-fatal)
        if self.warnings:
            print("\n" + "=" * 80, file=sys.stderr)
            print("⚠️  WARNINGS", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            for warning in self.warnings:
                print(f"\n{warning}", file=sys.stderr)

        # Print errors (fatal)
        if self.errors:
            print("\n" + "=" * 80, file=sys.stderr)
            print("❌ TEMPLATE SYNC ERRORS DETECTED", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            print(
                "\nThe repository does not match the template structure.",
                file=sys.stderr,
            )
            print(f"Template path: {self.template_path}", file=sys.stderr)
            print(f"Repository path: {self.repo_root}", file=sys.stderr)
            print(f"\nFound {len(self.errors)} error(s):\n", file=sys.stderr)

            for error in self.errors:
                print(error, file=sys.stderr)
                print("-" * 80, file=sys.stderr)

            print("\n" + "=" * 80, file=sys.stderr)
            print("💡 HOW TO FIX:", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            print(
                """
1. Review each error above to understand what's missing or different
2. For missing directories: Create them to match the template structure
3. For missing files: Copy them from the template directory
4. For mismatched files: Update them to match the template version
5. Re-run the hook to verify all issues are resolved

The template ensures your repository follows the latest best practices
and includes all necessary support files for OpenTofu modules.
""",
                file=sys.stderr,
            )
            print("=" * 80 + "\n", file=sys.stderr)
        elif not self.warnings:
            print(
                "✅ Repository structure matches template perfectly!",
                file=sys.stderr,
            )


def main() -> int:
    """Main entry point for the pre-commit hook."""
    parser = argparse.ArgumentParser(
        description="Check that repository scaffold files match a reference template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check repository against a template directory
  %(prog)s --template-path ~/templates/opentofu-module

  # Check with custom repository root
  %(prog)s --template-path /path/to/template --repo-root /path/to/repo

  # Can also pass specific files (for pre-commit framework compatibility)
  %(prog)s --template-path /path/to/template file1.txt file2.txt
        """,
    )
    parser.add_argument(
        "--template-path",
        required=True,
        help="Path to the template directory containing reference files",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the repository root (default: current directory)",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to check (optional, for pre-commit framework compatibility)",
    )

    args = parser.parse_args()

    try:
        checker = TemplateSyncChecker(
            template_path=args.template_path,
            repo_root=args.repo_root,
        )

        if checker.check_sync():
            checker.print_results()
            return 0
        else:
            checker.print_results()
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
