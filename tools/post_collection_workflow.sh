#!/usr/bin/env bash
#
# post_collection_workflow.sh - Automated workflow after crypto2 collection completes
#
# Purpose: Automatically analyze, validate, and prepare collected data for merging
#
# Usage:
#   ./tools/post_collection_workflow.sh data/raw/crypto2/scenario_b_full_*.csv

set -euo pipefail

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <path_to_collected_csv>"
    exit 1
fi

INPUT_FILE="$1"

# Verify file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}ERROR: File not found: $INPUT_FILE${NC}"
    exit 1
fi

echo ""
echo "========================================================================"
echo "crypto2 Post-Collection Workflow"
echo "========================================================================"
echo ""
echo "Input file: $INPUT_FILE"
echo "Started: $(date)"
echo ""

# Step 1: File size and basic stats
echo "========================================================================"
echo "Step 1: Basic File Statistics"
echo "========================================================================"
echo ""

FILE_SIZE=$(du -h "$INPUT_FILE" | awk '{print $1}')
RECORD_COUNT=$(wc -l < "$INPUT_FILE")
RECORD_COUNT=$((RECORD_COUNT - 1)) # Subtract header

echo "File size:     $FILE_SIZE"
echo "Record count:  $(printf "%'d" $RECORD_COUNT)"
echo ""

if [ $RECORD_COUNT -lt 50000 ]; then
    echo -e "${YELLOW}⚠️  WARNING: Record count seems low (<50,000). Expected >100,000 for 500 coins.${NC}"
    echo ""
fi

# Step 2: Coverage Analysis
echo "========================================================================"
echo "Step 2: Coverage Analysis (R)"
echo "========================================================================"
echo ""

if command -v Rscript &> /dev/null; then
    echo "Running coverage analysis..."
    Rscript tools/analyze_crypto2_coverage.R "$INPUT_FILE" | tee "validation/reports/crypto2_coverage_analysis_$(date +%Y%m%d_%H%M%S).txt"
    echo ""
    echo -e "${GREEN}✅ Coverage analysis complete${NC}"
else
    echo -e "${YELLOW}⚠️  R not found - skipping coverage analysis${NC}"
fi

echo ""

# Step 3: Bias Prevention Validation
echo "========================================================================"
echo "Step 3: Bias Prevention Validation (Python)"
echo "========================================================================"
echo ""

if [ -f "validation/scripts/validate_bias_prevention.py" ]; then
    echo "Running bias prevention tests..."

    if uv run validation/scripts/validate_bias_prevention.py "$INPUT_FILE"; then
        echo ""
        echo -e "${GREEN}✅ Bias prevention validation PASSED${NC}"
    else
        echo ""
        echo -e "${RED}❌ Bias prevention validation FAILED${NC}"
        echo "See logs for details"
    fi
else
    echo -e "${YELLOW}⚠️  Validation script not found - skipping${NC}"
fi

echo ""

# Step 4: Quick Quality Checks (Python)
echo "========================================================================"
echo "Step 4: Quick Quality Checks"
echo "========================================================================"
echo ""

echo "Running quick data quality checks..."

python3 - "$INPUT_FILE" <<'EOF'
import sys
import pandas as pd

input_file = sys.argv[1]
print(f"Loading data from: {input_file}")

df = pd.read_csv(input_file)
print(f"✅ Loaded {len(df):,} records\n")

print("Column Completeness:")
for col in ['timestamp', 'symbol', 'price', 'market_cap', 'circulating_supply', 'volume_24h']:
    if col in df.columns:
        non_null_pct = (df[col].notna().sum() / len(df)) * 100
        print(f"  {col:20s}: {non_null_pct:6.2f}% present")
    else:
        print(f"  {col:20s}: MISSING")

print(f"\nUnique coins: {df['symbol'].nunique()}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

# Check for circulating_supply presence (critical for verified tier)
if 'circulating_supply' in df.columns:
    supply_pct = (df['circulating_supply'].notna().sum() / len(df)) * 100
    if supply_pct >= 95:
        print(f"\n✅ Excellent: {supply_pct:.1f}% of records have circulating_supply")
    elif supply_pct >= 75:
        print(f"\n⚠️  Good: {supply_pct:.1f}% of records have circulating_supply")
    else:
        print(f"\n⚠️  Warning: Only {supply_pct:.1f}% of records have circulating_supply")
else:
    print("\n❌ ERROR: circulating_supply column missing!")

print("")
EOF

echo ""

# Step 5: Summary and Next Steps
echo "========================================================================"
echo "Step 5: Summary and Next Steps"
echo "========================================================================"
echo ""

echo -e "${GREEN}✅ Post-collection workflow complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review coverage analysis report in validation/reports/"
echo "  2. Review bias prevention validation results"
echo "  3. If all tests pass, proceed to CoinGecko collection"
echo "  4. Run: uv run validation/scripts/validate_coingecko.py <coingecko_data>"
echo "  5. Merge datasets: uv run tools/merge_datasets.py"
echo ""
echo "Completed: $(date)"
echo ""
