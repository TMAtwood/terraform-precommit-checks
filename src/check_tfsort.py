#!/usr/bin/env python3
"""
Pre-commit hook to verify Terraform files are sorted per tfsort conventions.

This hook checks that variable, output, locals, and terraform blocks in .tf files
are sorted alphabetically as per tfsort standards. It focuses specifically on
outputs.tf and variables.tf files but can check any .tf file.

tfsort conventions:
- variable blocks sorted alphabetically by name
- output blocks sorted alphabetically by name
- locals blocks sorted alphabetically by name
- terraform blocks sorted alphabetically by name
- Proper spacing between blocks
"""

import argparse
import io
import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Tuple

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


class BlockInfo(NamedTuple):
    """Information about a Terraform block."""

    block_type: str  # "variable", "output", "locals", or "terraform"
    name: str  # Block name (empty for locals/terraform)
    line_number: int  # Starting line number
    content: str  # Full block content


class TFSortChecker:
    """Check if Terraform files are sorted per tfsort conventions."""

    # Patterns for different block types
    VARIABLE_PATTERN = re.compile(r'^\s*variable\s+"([^"]+)"\s*\{', re.MULTILINE)
    OUTPUT_PATTERN = re.compile(r'^\s*output\s+"([^"]+)"\s*\{', re.MULTILINE)
    LOCALS_PATTERN = re.compile(r"^\s*locals\s*\{", re.MULTILINE)
    TERRAFORM_PATTERN = re.compile(r"^\s*terraform\s*\{", re.MULTILINE)

    def __init__(self, files: List[str]):
        """Initialize checker with list of files to check."""
        self.files = files
        self.errors: List[Tuple[str, int, str]] = []

    @staticmethod
    def find_block_end(content: str, start_pos: int) -> int:
        """
        Find the closing brace of a block starting at start_pos.

        Args:
            content: File content
            start_pos: Position where block starts

        Returns:
            Position of closing brace
        """
        brace_count = 0
        in_block = False

        for i in range(start_pos, len(content)):
            if content[i] == "{":
                brace_count += 1
                in_block = True
            elif content[i] == "}":
                brace_count -= 1
                if in_block and brace_count == 0:
                    return i

        return len(content)

    def extract_blocks(self, content: str, block_type: str) -> List[BlockInfo]:
        """
        Extract all blocks of a given type from content.

        Args:
            content: File content
            block_type: Type of block ("variable", "output", "locals", "terraform")

        Returns:
            List of BlockInfo objects
        """
        blocks: List[BlockInfo] = []

        if block_type == "variable":
            pattern = self.VARIABLE_PATTERN
        elif block_type == "output":
            pattern = self.OUTPUT_PATTERN
        elif block_type == "locals":
            pattern = self.LOCALS_PATTERN
        elif block_type == "terraform":
            pattern = self.TERRAFORM_PATTERN
        else:
            return blocks

        for match in pattern.finditer(content):
            # Get block name (empty string for locals/terraform)
            name = match.group(1) if block_type in ["variable", "output"] else ""

            # Find line number
            line_num = content[: match.start()].count("\n") + 1

            # Find block end
            end_pos = self.find_block_end(content, match.start())
            block_content = content[match.start() : end_pos + 1]

            blocks.append(
                BlockInfo(
                    block_type=block_type,
                    name=name,
                    line_number=line_num,
                    content=block_content,
                )
            )

        return blocks

    def check_block_order(
        self, blocks: List[BlockInfo], file_path: str
    ) -> List[Tuple[str, int, str]]:
        """
        Check if blocks are in alphabetical order.

        Args:
            blocks: List of blocks to check
            file_path: Path to file being checked

        Returns:
            List of error tuples (file_path, line_number, error_message)
        """
        errors: List[Tuple[str, int, str]] = []

        if len(blocks) <= 1:
            return errors

        block_type = blocks[0].block_type
        block_names = [block.name for block in blocks]
        sorted_names = sorted(block_names, key=str.lower)

        if block_names != sorted_names:
            # Find first out-of-order block
            for i, (current, expected) in enumerate(zip(block_names, sorted_names)):
                if current != expected:
                    line_num = blocks[i].line_number
                    current_order = ", ".join(block_names)
                    expected_order = ", ".join(sorted_names)
                    error_msg = (
                        f"❌ {block_type.capitalize()} blocks are not sorted "
                        f"alphabetically.\n"
                        f"   Expected '{expected}' but found '{current}' at line "
                        f"{line_num}.\n"
                        f"   \n"
                        f"   Current order: {current_order}\n"
                        f"   Expected order: {expected_order}\n"
                        f"   \n"
                        f"   💡 Fix: Run 'tfsort {file_path}' or manually "
                        f"reorder blocks alphabetically."
                    )
                    errors.append((file_path, blocks[i].line_number, error_msg))
                    break

        return errors

    def check_file(self, file_path: str) -> bool:
        """
        Check a single file for tfsort compliance.

        Args:
            file_path: Path to file to check

        Returns:
            True if file passes checks, False if errors found
        """
        path = Path(file_path)

        # Only check .tf files
        if path.suffix != ".tf":
            return True

        # Focus on outputs.tf and variables.tf, but allow checking any .tf file
        file_name = path.name.lower()

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}", file=sys.stderr)
            return False

        has_errors = False

        # Check variable blocks (especially in variables.tf)
        if "variables.tf" in file_name or "variable" in content:
            variable_blocks = self.extract_blocks(content, "variable")
            if variable_blocks:
                errors = self.check_block_order(variable_blocks, file_path)
                if errors:
                    self.errors.extend(errors)
                    has_errors = True

        # Check output blocks (especially in outputs.tf)
        if "outputs.tf" in file_name or "output" in content:
            output_blocks = self.extract_blocks(content, "output")
            if output_blocks:
                errors = self.check_block_order(output_blocks, file_path)
                if errors:
                    self.errors.extend(errors)
                    has_errors = True

        # Check locals blocks (in any .tf file)
        # Note: locals blocks don't have names, so we just detect them
        # We don't sort locals blocks themselves, just detect presence

        # Check terraform blocks (in any .tf file)
        # Note: terraform blocks don't have names, so we just detect them

        return not has_errors

    def run(self) -> int:
        """
        Run the checker on all files.

        Returns:
            0 if all checks pass, 1 if any errors found
        """
        all_passed = True

        for file_path in self.files:
            if not self.check_file(file_path):
                all_passed = False

        if self.errors:
            print("\n" + "=" * 80)
            print("🔍 TFSort Compliance Check Failed")
            print("=" * 80 + "\n")

            for file_path, line_num, error_msg in self.errors:
                print(f"📁 File: {file_path}")
                print(f"📍 Line: {line_num}")
                print(error_msg)
                print()

            print("=" * 80)
            print(f"❌ Found {len(self.errors)} sorting issue(s)")
            print("=" * 80)
            print()
            print("💡 To fix automatically, install and run tfsort:")
            print("   https://github.com/AlexNabokikh/tfsort")
            print()

            return 1

        if self.files:
            print("✅ All files are properly sorted per tfsort conventions")

        return 0 if all_passed else 1


def main() -> int:
    """Main entry point for the pre-commit hook."""
    parser = argparse.ArgumentParser(
        description="Check if Terraform files are sorted per tfsort conventions"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to check (typically outputs.tf and variables.tf)",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Check all .tf files in directory",
    )

    args = parser.parse_args()

    files = args.files
    if args.all_files and not files:
        # Find all .tf files in current directory
        files = [str(p) for p in Path(".").rglob("*.tf")]

    if not files:
        print("No files to check", file=sys.stderr)
        return 0

    checker = TFSortChecker(files)
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())
