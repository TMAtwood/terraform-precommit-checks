#!/usr/bin/env bash

set -e

# Script: create_version_tag.sh
# Purpose: Create a version tag and move the 'latest' tag to it
# Usage: ./create_version_tag.sh <MajorMinorPatch>
# Example: ./create_version_tag.sh 1.0.0

if [[ $# -eq 0 ]]; then
    # Try to get version from GitVersion
    if command -v gitversion &> /dev/null; then
        VERSION=$(gitversion /showvariable MajorMinorPatch)
        echo "No version provided, using GitVersion: $VERSION"
    else
        echo "Usage: $0 [MajorMinorPatch]"
        echo "Example: $0 1.0.0"
        echo ""
        echo "If no version is provided, GitVersion must be installed and available."
        exit 1
    fi
elif [[ $# -eq 1 ]]; then
    VERSION=$1
else
    echo "Usage: $0 [MajorMinorPatch]"
    echo "Example: $0 1.0.0"
    exit 1
fi
VERSION_TAG="v${VERSION}"

# Validate version format (basic check for semantic versioning)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Invalid version format. Expected MajorMinorPatch (e.g., 1.0.0)"
    exit 1
fi

echo "Creating version tag: $VERSION_TAG"

# Check if version tag already exists
if git rev-parse "$VERSION_TAG" >/dev/null 2>&1; then
    echo "Error: Tag $VERSION_TAG already exists"
    exit 1
fi

# Create the version tag
git tag -a "$VERSION_TAG" -m "Release $VERSION_TAG"
echo "✓ Created tag $VERSION_TAG"

# # Delete the previous 'latest' tag from remote first
# echo "Removing previous 'latest' tag from remote..."
# git push origin :refs/tags/latest 2>/dev/null || true
# echo "✓ Deleted previous 'latest' tag from remote"

# # Delete the local 'latest' tag if it exists
# if git rev-parse latest >/dev/null 2>&1; then
#     git tag -d latest
#     echo "✓ Deleted previous 'latest' tag locally"
# fi

# # Create 'latest' tag pointing to the new version tag
# git tag -a latest -m "Latest release: $VERSION_TAG"
# echo "✓ Created 'latest' tag pointing to $VERSION_TAG"

# Push tags to remote
echo "Pushing tags to remote..."
git push origin "$VERSION_TAG"
# git push origin latest
echo "✓ Tag pushed to remote"

echo ""
echo "Success! Version $VERSION_TAG is now tagged."
