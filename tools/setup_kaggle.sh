#!/bin/bash
# Kaggle API Setup Helper
# ADR: 0001-hybrid-free-data-acquisition

set -e

echo "========================================="
echo "Kaggle API Setup Helper"
echo "========================================="
echo ""

# Check if Kaggle CLI is installed
if ! .venv/bin/kaggle --version > /dev/null 2>&1; then
    echo "❌ Kaggle CLI not found in venv"
    echo "Installing dependencies..."
    uv sync
fi

echo "✅ Kaggle CLI installed: $(.venv/bin/kaggle --version)"
echo ""

# Check for API key
if [ -f ~/.kaggle/kaggle.json ]; then
    echo "✅ Kaggle API credentials found at ~/.kaggle/kaggle.json"
    echo ""
    echo "Testing credentials..."
    if .venv/bin/kaggle datasets list --max-size 1 > /dev/null 2>&1; then
        echo "✅ Credentials valid!"
        echo ""
        echo "Ready to download dataset."
        echo "Run: ./tools/download_kaggle_dataset.sh"
    else
        echo "❌ Credentials exist but may be invalid"
        echo "Please regenerate API key from https://www.kaggle.com/account"
    fi
else
    echo "❌ Kaggle API credentials not found"
    echo ""
    echo "Setup instructions:"
    echo "1. Go to https://www.kaggle.com/account"
    echo "2. Scroll to 'API' section"
    echo "3. Click 'Create New API Token'"
    echo "4. Save the downloaded kaggle.json file:"
    echo "   mkdir -p ~/.kaggle"
    echo "   mv ~/Downloads/kaggle.json ~/.kaggle/"
    echo "   chmod 600 ~/.kaggle/kaggle.json"
    echo ""
    echo "5. Run this script again to verify"
fi

echo ""
echo "========================================="
