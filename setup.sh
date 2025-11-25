#!/usr/bin/env bash
# Setup script for installing the provider configuration pre-commit hook

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Provider Config Pre-Commit Hook Setup"
echo "=========================================="
echo ""

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "❌ pre-commit is not installed."
    echo ""
    echo "Install it with:"
    echo "  pip install pre-commit"
    echo ""
    echo "Or with pipx:"
    echo "  pipx install pre-commit"
    echo ""
    exit 1
fi

echo "✅ pre-commit is installed"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    echo "Please run this script from the root of your git repository"
    exit 1
fi

echo "✅ Git repository detected"
echo ""

# Copy the checker script if it doesn't exist
if [ ! -f "check_provider_config.py" ]; then
    if [ -f "$SCRIPT_DIR/check_provider_config.py" ]; then
        cp "$SCRIPT_DIR/check_provider_config.py" .
        chmod +x check_provider_config.py
        echo "✅ Copied check_provider_config.py to repository root"
    else
        echo "❌ Could not find check_provider_config.py"
        exit 1
    fi
else
    echo "✅ check_provider_config.py already exists"
fi
echo ""

# Create or update .pre-commit-config.yaml
if [ ! -f ".pre-commit-config.yaml" ]; then
    cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: local
    hooks:
      - id: check-provider-config
        name: Check for old-style provider configurations
        entry: python check_provider_config.py
        language: python
        files: \.tf$
        pass_filenames: true
        description: |
          Detects old-style provider configurations that prevent module-level
          for_each and depends_on in Terraform/OpenTofu modules.
EOF
    echo "✅ Created .pre-commit-config.yaml"
else
    echo "ℹ️  .pre-commit-config.yaml already exists"
    echo "   Please manually add the check-provider-config hook if needed"
fi
echo ""

# Install the pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install
echo "✅ Pre-commit hooks installed"
echo ""

# Run the hook on all files as a test
echo "Testing on all .tf files..."
if pre-commit run check-provider-config --all-files; then
    echo ""
    echo "=========================================="
    echo "✅ Setup Complete!"
    echo "=========================================="
    echo ""
    echo "All .tf files passed the check."
else
    echo ""
    echo "=========================================="
    echo "⚠️  Setup Complete with Warnings"
    echo "=========================================="
    echo ""
    echo "Some .tf files have old-style provider configurations."
    echo "Please review the errors above and update your modules."
    echo ""
    echo "The pre-commit hook is now active and will prevent"
    echo "commits with old-style provider configurations."
fi

echo ""
echo "Next steps:"
echo "1. Review any errors from the test run above"
echo "2. Update modules to use required_providers pattern"
echo "3. The hook will now run automatically on every commit"
echo ""
echo "To run manually: pre-commit run check-provider-config --all-files"
echo "To bypass (not recommended): git commit --no-verify"
echo ""
