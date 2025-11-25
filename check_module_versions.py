#!/usr/bin/env python3
"""
Pre-commit hook to detect conflicting module versions/hashes in Terraform/OpenTofu.

This hook ensures that when the same module is referenced multiple times,
all references use the same version, git ref, or commit hash. Conflicting
versions can lead to inconsistent behavior and maintenance issues.
"""

import argparse
import io
import re
import sys
from typing import Dict, List, NamedTuple, Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


class ModuleReference(NamedTuple):
    """Represents a module reference with its version/ref information."""

    file_path: str
    line_number: int
    source: str
    version: Optional[str]
    git_ref: Optional[str]
    normalized_source: str


class ModuleVersionChecker:
    """Checker for detecting conflicting module versions."""

    # Pattern to match module blocks
    MODULE_BLOCK_PATTERN = re.compile(r'^\s*module\s+"([^"]+)"\s*\{', re.MULTILINE)

    # Pattern to match source within module block
    SOURCE_PATTERN = re.compile(r'^\s*source\s*=\s*"([^"]+)"', re.MULTILINE)

    # Pattern to match version within module block
    VERSION_PATTERN = re.compile(r'^\s*version\s*=\s*"([^"]+)"', re.MULTILINE)

    # Pattern to extract git ref from source URL
    GIT_REF_PATTERN = re.compile(r"\?(ref|tag)=([^&]+)|//.*\?.*ref=([^&]+)|\.git//.*\?ref=([^&]+)")

    # Pattern to extract git commit hash from source
    GIT_COMMIT_PATTERN = re.compile(r"[?&]commit=([a-f0-9]{7,40})")

    def __init__(self) -> None:
        """Initialize the checker."""
        self.module_references: Dict[str, List[ModuleReference]] = {}

    @staticmethod
    def normalize_source(source: str) -> str:
        """
        Normalize a module source to identify the same module.

        Removes git refs, versions, and trailing slashes for comparison.

        Args:
            source: Raw module source string

        Returns:
            Normalized source string
        """
        # Remove git refs and commits
        normalized = re.sub(r"\?(ref|tag|commit)=[^&]+", "", source)
        normalized = re.sub(r"&(ref|tag|commit)=[^&]+", "", normalized)

        # Remove trailing ? if no query params remain
        normalized = re.sub(r"\?$", "", normalized)

        # Remove trailing slashes
        normalized = normalized.rstrip("/")

        # For git sources, remove the protocol differences
        normalized = re.sub(r"^git::", "", normalized)
        normalized = re.sub(r"^https?::", "", normalized)

        return normalized

    @staticmethod
    def extract_git_ref(source: str) -> Optional[str]:
        """
        Extract git ref/tag/commit from module source.

        Args:
            source: Module source string

        Returns:
            Git ref, tag, or commit hash if found
        """
        # Check for commit hash
        commit_match = ModuleVersionChecker.GIT_COMMIT_PATTERN.search(source)
        if commit_match:
            return f"commit={commit_match.group(1)}"

        # Check for ref or tag
        ref_match = ModuleVersionChecker.GIT_REF_PATTERN.search(source)
        if ref_match:
            # The pattern captures in different groups depending on format
            for group in ref_match.groups():
                if group and group not in ("ref", "tag"):
                    return group

        return None

    def parse_module_block(
        self, content: str, start_pos: int, file_path: str, start_line: int
    ) -> Optional[ModuleReference]:
        """
        Parse a module block to extract source and version information.

        Args:
            content: File content
            start_pos: Starting position of module block
            file_path: Path to the file
            start_line: Line number where module block starts

        Returns:
            ModuleReference if valid module found, None otherwise
        """
        # Find the closing brace for this module block
        brace_count = 1
        pos = start_pos
        while pos < len(content) and brace_count > 0:
            if content[pos] == "{":
                brace_count += 1
            elif content[pos] == "}":
                brace_count -= 1
            pos += 1

        if brace_count != 0:
            # Malformed block
            return None

        module_content = content[start_pos:pos]

        # Extract source
        source_match = self.SOURCE_PATTERN.search(module_content)
        if not source_match:
            return None

        source = source_match.group(1)

        # Skip local path modules (relative or absolute paths)
        if source.startswith("./") or source.startswith("../") or source.startswith("/"):
            return None

        # Extract version (for registry modules)
        version_match = self.VERSION_PATTERN.search(module_content)
        version = version_match.group(1) if version_match else None

        # Extract git ref/tag/commit (for git sources)
        git_ref = self.extract_git_ref(source)

        # Normalize source for comparison
        normalized_source = self.normalize_source(source)

        return ModuleReference(
            file_path=file_path,
            line_number=start_line,
            source=source,
            version=version,
            git_ref=git_ref,
            normalized_source=normalized_source,
        )

    def check_file(self, file_path: str) -> List[ModuleReference]:
        """
        Check a single Terraform file for module references.

        Args:
            file_path: Path to the .tf file

        Returns:
            List of module references found
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return []

        references = []

        # Find all module blocks
        for match in self.MODULE_BLOCK_PATTERN.finditer(content):
            # Calculate line number
            line_number = content[: match.start()].count("\n") + 1

            # Parse the module block
            module_ref = self.parse_module_block(content, match.end(), file_path, line_number)

            if module_ref:
                references.append(module_ref)

                # Add to tracking dictionary
                norm_source = module_ref.normalized_source
                if norm_source not in self.module_references:
                    self.module_references[norm_source] = []
                self.module_references[norm_source].append(module_ref)

        return references

    def find_conflicts(self) -> Dict[str, List[ModuleReference]]:
        """
        Find modules with conflicting versions/refs.

        Returns:
            Dictionary mapping module source to conflicting references
        """
        conflicts = {}

        for source, references in self.module_references.items():
            if len(references) < 2:
                continue

            # Collect all unique version identifiers
            versions = set()
            for ref in references:
                if ref.version:
                    versions.add(f"version={ref.version}")
                elif ref.git_ref:
                    versions.add(ref.git_ref)
                else:
                    # No version specified
                    versions.add("no-version")

            # If more than one unique version, we have a conflict
            if len(versions) > 1:
                conflicts[source] = references

        return conflicts

    def format_conflict_report(self, conflicts: Dict[str, List[ModuleReference]]) -> str:
        """
        Format conflicts into a human-readable report.

        Args:
            conflicts: Dictionary of conflicting module references

        Returns:
            Formatted report string
        """
        if not conflicts:
            return ""

        lines = []
        lines.append("=" * 80)
        lines.append("❌ MODULE VERSION CONFLICTS DETECTED")
        lines.append("=" * 80)
        lines.append("")
        lines.append("The same module is referenced with different versions or git refs.")
        lines.append("This can lead to inconsistent behavior and should be resolved.")
        lines.append("")

        for source, references in sorted(conflicts.items()):
            lines.append(f"📦 Module: {source}")
            lines.append("   Conflicting references:")
            lines.append("")

            for ref in references:
                version_info = ""
                if ref.version:
                    version_info = f"version = {ref.version}"
                elif ref.git_ref:
                    version_info = f"git ref = {ref.git_ref}"
                else:
                    version_info = "no version specified"

                lines.append(f"   📁 File: {ref.file_path}")
                lines.append(f"   📍 Line: {ref.line_number}")
                lines.append(f"   🔖 Version: {version_info}")
                lines.append(f"   🔗 Source: {ref.source}")
                lines.append("")

            lines.append("   ⚠️  Resolution:")
            lines.append("   All references to this module should use the same version/ref.")
            lines.append("   Choose one version and update all references to match.")
            lines.append("")
            lines.append("-" * 80)
            lines.append("")

        return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the module version checker.

    Args:
        argv: Command line arguments

    Returns:
        Exit code (0 for success, 1 for conflicts found)
    """
    parser = argparse.ArgumentParser(
        description="Check for conflicting module versions in Terraform/OpenTofu files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check specific files
  python check_module_versions.py main.tf modules.tf

  # Check all .tf files (via pre-commit)
  pre-commit run check-module-versions --all-files

  # Use in CI/CD pipeline
  find . -name "*.tf" -exec python check_module_versions.py {} +
        """,
    )

    parser.add_argument("filenames", nargs="*", help="Terraform files to check")

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output including all module references",
    )

    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Exclude files in directories matching this pattern (can be used multiple times)",
    )

    args = parser.parse_args(argv)

    if not args.filenames:
        print("No files provided to check.")
        return 0

    # Filter out files in excluded directories
    filtered_filenames = []
    for filename in args.filenames:
        excluded = False
        for exclude_pattern in args.exclude_dir:
            if exclude_pattern in filename.replace("\\", "/"):
                excluded = True
                break
        if not excluded:
            filtered_filenames.append(filename)

    if args.verbose and len(filtered_filenames) < len(args.filenames):
        print(f"Excluded {len(args.filenames) - len(filtered_filenames)} file(s)")

    checker = ModuleVersionChecker()

    # Check all files
    total_refs = 0
    for filename in filtered_filenames:
        refs = checker.check_file(filename)
        total_refs += len(refs)

    if args.verbose:
        print(f"✓ Scanned {len(filtered_filenames)} files")
        print(f"✓ Found {total_refs} module references")
        print(f"✓ Checking {len(checker.module_references)} unique modules")
        print("")

    # Find conflicts
    conflicts = checker.find_conflicts()

    if conflicts:
        report = checker.format_conflict_report(conflicts)
        print(report)
        print(f"❌ Found {len(conflicts)} module(s) with version conflicts")
        return 1

    if args.verbose or total_refs > 0:
        print("✅ No module version conflicts detected!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
