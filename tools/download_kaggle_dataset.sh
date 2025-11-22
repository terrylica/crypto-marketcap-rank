#!/bin/bash
# Download Kaggle Dataset Script
# ADR: 0001-hybrid-free-data-acquisition

set -e

DATASET="bizzyvinci/coinmarketcap-historical-data"
OUTPUT_DIR="data/raw/kaggle"
LOG_FILE="logs/0001-kaggle-download-$(date +%Y%m%d_%H%M%S).log"

echo "=========================================" | tee "$LOG_FILE"
echo "Kaggle Dataset Download" | tee -a "$LOG_FILE"
echo "=========================================" | tee -a "$LOG_FILE"
echo "Dataset: $DATASET" | tee -a "$LOG_FILE"
echo "Output: $OUTPUT_DIR" | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check credentials
if [ ! -f ~/.kaggle/kaggle.json ]; then
    echo "❌ ERROR: Kaggle credentials not found" | tee -a "$LOG_FILE"
    echo "Run: ./tools/setup_kaggle.sh" | tee -a "$LOG_FILE"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Download dataset
echo "Downloading dataset (820 MB, ~5-10 minutes)..." | tee -a "$LOG_FILE"
.venv/bin/kaggle datasets download -d "$DATASET" -p "$OUTPUT_DIR" 2>&1 | tee -a "$LOG_FILE"

# Extract
echo "" | tee -a "$LOG_FILE"
echo "Extracting..." | tee -a "$LOG_FILE"
unzip -o "$OUTPUT_DIR/coinmarketcap-historical-data.zip" -d "$OUTPUT_DIR" 2>&1 | tee -a "$LOG_FILE"

# Cleanup zip
rm -f "$OUTPUT_DIR/coinmarketcap-historical-data.zip"

# Verify
echo "" | tee -a "$LOG_FILE"
echo "✅ Download complete!" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Files:" | tee -a "$LOG_FILE"
ls -lh "$OUTPUT_DIR" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=========================================" | tee -a "$LOG_FILE"
echo "Next step: Run validation" | tee -a "$LOG_FILE"
echo "  uv run validation/scripts/validate_kaggle.py $OUTPUT_DIR/historical_data.csv" | tee -a "$LOG_FILE"
echo "=========================================" | tee -a "$LOG_FILE"
