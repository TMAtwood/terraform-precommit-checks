#!/usr/bin/env python3
"""
Pre-commit hook to verify Terraform files are sorted per tfsort conventions.

This hook checks that .tf files are properly sorted according to tfsort standards.
It uses the actual tfsort binary (if available) for accurate validation, or falls
back to a built-in block order check if tfsort is not installed.

tfsort conventions:
- variable blocks sorted alphabetically by name
- output blocks sorted alphabetically by name
- locals blocks sorted alphabetically by name
- terraform blocks sorted alphabetically by name
- Proper spacing between blocks
- No unnecessary leading or trailing newlines

Reference: https://github.com/AlexNabokikh/tfsort
"""

import argparse
import difflib
import io
import re
import shutil
import subprocess  # nosec B404 - subprocess is used safely with list arguments
import sys
from pathlib import Path
from typing import NamedTuple

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

    def __init__(self, files: list[str], use_tfsort_binary: bool = True):
        """Initialize checker with list of files to check.

        Args:
            files: List of file paths to check
            use_tfsort_binary: Whether to use the tfsort binary if available.
                             If False, uses built-in block order checking only.
        """
        self.files = files
        self.errors: list[tuple[str, int, str]] = []
        self.use_tfsort_binary = use_tfsort_binary
        self._tfsort_path: str | None = None
        self._tfsort_checked = False

    def _find_tfsort(self) -> str | None:
        """Find the tfsort binary in PATH.

        Returns:
            Path to tfsort binary if found, None otherwise.
        """
        if self._tfsort_checked:
            return self._tfsort_path

        self._tfsort_checked = True
        self._tfsort_path = shutil.which("tfsort")
        return self._tfsort_path

    def _check_with_tfsort_binary(self, file_path: str) -> tuple[bool, str] | None:
        """Check a file using the tfsort binary's dry-run mode.

        Args:
            file_path: Path to the file to check

        Returns:
            Tuple of (is_sorted, diff_output) if tfsort ran successfully,
            None if tfsort is not available or failed.
        """
        if not self.use_tfsort_binary:
            return None

        tfsort_path = self._find_tfsort()
        if not tfsort_path:
            return None

        try:
            # Read original file content
            path = Path(file_path)
            original_content = path.read_text(encoding="utf-8")

            # Run tfsort in dry-run mode to get what the sorted output would be
            # tfsort --dry-run outputs the sorted content to stdout
            result = subprocess.run(  # nosec B603 - arguments are list (not shell injection risk)
                [tfsort_path, "--dry-run", str(path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # tfsort returns 0 on success
            if result.returncode != 0:
                # If tfsort fails, fall back to built-in checking
                return None

            sorted_content = result.stdout

            # Compare original with sorted
            if original_content == sorted_content:
                return (True, "")

            # Generate a diff for helpful output
            original_lines = original_content.splitlines(keepends=True)
            sorted_lines = sorted_content.splitlines(keepends=True)

            diff = list(
                difflib.unified_diff(
                    original_lines,
                    sorted_lines,
                    fromfile=f"{file_path} (current)",
                    tofile=f"{file_path} (after tfsort)",
                    lineterm="",
                )
            )

            diff_output = "".join(diff)
            return (False, diff_output)

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            # If anything goes wrong, fall back to built-in checking
            return None

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

    def extract_blocks(self, content: str, block_type: str) -> list[BlockInfo]:
        """
        Extract all blocks of a given type from content.

        Args:
            content: File content
            block_type: Type of block ("variable", "output", "locals", "terraform")

        Returns:
            List of BlockInfo objects
        """
        blocks: list[BlockInfo] = []

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
        self, blocks: list[BlockInfo], file_path: str
    ) -> list[tuple[str, int, str]]:
        """
        Check if blocks are in alphabetical order.

        Args:
            blocks: List of blocks to check
            file_path: Path to file being checked

        Returns:
            List of error tuples (file_path, line_number, error_message)
        """
        errors: list[tuple[str, int, str]] = []

        if len(blocks) <= 1:
            return errors

        block_type = blocks[0].block_type
        block_names = [block.name for block in blocks]
        sorted_names = sorted(block_names, key=str.lower)

        if block_names != sorted_names:
            # Find first out-of-order block
            for i, (current, expected) in enumerate(zip(block_names, sorted_names, strict=True)):
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

    def _check_file_with_builtin(self, file_path: str, content: str) -> bool:
        """
        Check a file using built-in block order checking.

        This is used as a fallback when tfsort binary is not available.
        Note: This only checks block order, not spacing or formatting.

        Args:
            file_path: Path to file to check
            content: File content

        Returns:
            True if file passes checks, False if errors found
        """
        file_name = Path(file_path).name.lower()
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

        return not has_errors

    def check_file(self, file_path: str) -> bool:
        """
        Check a single file for tfsort compliance.

        Uses the tfsort binary if available for comprehensive checking
        (block order, spacing, formatting). Falls back to built-in
        block order checking if tfsort is not installed.

        Args:
            file_path: Path to file to check

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
            print(f"❌ Error reading {file_path}: {e}", file=sys.stderr)
            return False

        # Try using tfsort binary first (most comprehensive)
        tfsort_result = self._check_with_tfsort_binary(file_path)

        if tfsort_result is not None:
            is_sorted, diff_output = tfsort_result
            if is_sorted:
                return True
            else:
                # File is not sorted - record the error with diff
                error_msg = (
                    "❌ File is not properly sorted per tfsort conventions.\n"
                    "   \n"
                    "   The following changes would be made by tfsort:\n"
                    "   \n"
                )
                # Indent the diff for readability
                if diff_output:
                    diff_lines = diff_output.split("\n")
                    # Limit diff output to first 30 lines to avoid overwhelming output
                    if len(diff_lines) > 30:
                        diff_preview = "\n".join(diff_lines[:30])
                        diff_preview += f"\n   ... ({len(diff_lines) - 30} more lines)"
                    else:
                        diff_preview = diff_output
                    error_msg += f"   {diff_preview.replace(chr(10), chr(10) + '   ')}\n"
                error_msg += (
                    f"   \n   💡 Fix: Run 'tfsort {file_path}' to automatically sort the file."
                )
                self.errors.append((file_path, 1, error_msg))
                return False

        # Fall back to built-in checking (block order only)
        return self._check_file_with_builtin(file_path, content)

    def run(self) -> int:
        """
        Run the checker on all files.

        Returns:
            0 if all checks pass, 1 if any errors found
        """
        all_passed = True

        # Show which mode we're using
        if self.use_tfsort_binary and self._find_tfsort():
            mode_msg = "Using tfsort binary for comprehensive checking"
        else:
            mode_msg = "Using built-in block order checking (tfsort not found)"

        for file_path in self.files:
            if not self.check_file(file_path):
                all_passed = False

        if self.errors:
            print("\n" + "=" * 80)
            print("🔍 TFSort Compliance Check Failed")
            print(f"   ({mode_msg})")
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
            print(f"   ({mode_msg})")

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
    parser.add_argument(
        "--no-tfsort-binary",
        action="store_true",
        help="Disable use of tfsort binary, use built-in checking only",
    )

    args = parser.parse_args()

    files = args.files
    if args.all_files and not files:
        # Find all .tf files in current directory
        files = [str(p) for p in Path(".").rglob("*.tf")]

    if not files:
        print("No files to check", file=sys.stderr)
        return 0

    use_tfsort = not args.no_tfsort_binary
    checker = TFSortChecker(files, use_tfsort_binary=use_tfsort)
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())
