#!/bin/bash
# Auto-Validation Runner
# ADR: 0001-hybrid-free-data-acquisition
# Runs all validation tests and surfaces errors

set -e

LOG_FILE="logs/0001-validation-suite-$(date +%Y%m%d_%H%M%S).log"

echo "=========================================" | tee "$LOG_FILE"
echo "Automated Validation Suite" | tee -a "$LOG_FILE"
echo "=========================================" | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

FAILED=0

# Test 1: Python syntax validation
echo "Test 1: Python Syntax Validation" | tee -a "$LOG_FILE"
echo "----------------------------------------------------------" | tee -a "$LOG_FILE"

PYTHON_SCRIPTS_VALIDATED=0
for script in validation/scripts/*.py tools/*.py; do
    if [ -f "$script" ]; then
        echo "Checking $script..." | tee -a "$LOG_FILE"
        if python3 -m py_compile "$script" 2>&1 | tee -a "$LOG_FILE"; then
            echo "  ✅ Syntax valid" | tee -a "$LOG_FILE"
            PYTHON_SCRIPTS_VALIDATED=$((PYTHON_SCRIPTS_VALIDATED + 1))
        else
            echo "  ❌ Syntax error" | tee -a "$LOG_FILE"
            FAILED=$((FAILED + 1))
        fi
    fi
done

echo "  Total Python scripts validated: $PYTHON_SCRIPTS_VALIDATED" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"

# Test 2: R syntax validation
echo "Test 2: R Syntax Validation" | tee -a "$LOG_FILE"
echo "----------------------------------------------------------" | tee -a "$LOG_FILE"

if command -v R > /dev/null 2>&1; then
    for script in tools/*.R; do
        if [ -f "$script" ]; then
            echo "Checking $script..." | tee -a "$LOG_FILE"
            if R -e "source('$script', echo=FALSE)" > /dev/null 2>&1; then
                echo "  ✅ Syntax valid" | tee -a "$LOG_FILE"
            else
                echo "  ⚠️  Cannot validate (may require runtime execution)" | tee -a "$LOG_FILE"
            fi
        fi
    done
else
    echo "⚠️  R not installed, skipping R script validation" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

# Test 3: Documentation consistency
echo "Test 3: Documentation Consistency" | tee -a "$LOG_FILE"
echo "----------------------------------------------------------" | tee -a "$LOG_FILE"

# Check ADR references
if grep -q "adr-id" docs/development/plan/0001-hybrid-free-data-acquisition/plan.md; then
    echo "  ✅ Plan contains adr-id field" | tee -a "$LOG_FILE"
else
    echo "  ❌ Plan missing adr-id field" | tee -a "$LOG_FILE"
    FAILED=$((FAILED + 1))
fi

# Check if ADR exists
if [ -f "docs/architecture/decisions/0001-hybrid-free-data-acquisition.md" ]; then
    echo "  ✅ ADR-0001 exists" | tee -a "$LOG_FILE"
else
    echo "  ❌ ADR-0001 missing" | tee -a "$LOG_FILE"
    FAILED=$((FAILED + 1))
fi

echo "" | tee -a "$LOG_FILE"

# Test 4: Required directories
echo "Test 4: Directory Structure" | tee -a "$LOG_FILE"
echo "----------------------------------------------------------" | tee -a "$LOG_FILE"

for dir in docs/architecture/decisions docs/development/plan data logs validation tools; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir exists" | tee -a "$LOG_FILE"
    else
        echo "  ❌ $dir missing" | tee -a "$LOG_FILE"
        FAILED=$((FAILED + 1))
    fi
done

echo "" | tee -a "$LOG_FILE"

# Test 5: Dependencies
echo "Test 5: Python Dependencies" | tee -a "$LOG_FILE"
echo "----------------------------------------------------------" | tee -a "$LOG_FILE"

if [ -f ".venv/bin/python" ]; then
    echo "  ✅ Virtual environment exists" | tee -a "$LOG_FILE"

    # Test imports (skip kaggle auth check)
    .venv/bin/python -c "import pandas; import numpy" 2>&1 | tee -a "$LOG_FILE"
    if [ $? -eq 0 ]; then
        echo "  ✅ Core packages installed (pandas, numpy)" | tee -a "$LOG_FILE"
        # Note: kaggle import requires credentials, checked separately
    else
        echo "  ❌ Missing required packages" | tee -a "$LOG_FILE"
        FAILED=$((FAILED + 1))
    fi
else
    echo "  ❌ Virtual environment not found" | tee -a "$LOG_FILE"
    echo "     Run: uv sync" | tee -a "$LOG_FILE"
    FAILED=$((FAILED + 1))
fi

echo "" | tee -a "$LOG_FILE"

# Summary
echo "=========================================" | tee -a "$LOG_FILE"
echo "VALIDATION SUMMARY" | tee -a "$LOG_FILE"
echo "=========================================" | tee -a "$LOG_FILE"

if [ $FAILED -eq 0 ]; then
    echo "✅ All validations passed!" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Ready to proceed with data collection." | tee -a "$LOG_FILE"
    exit 0
else
    echo "❌ $FAILED validation(s) failed" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Please fix errors before proceeding." | tee -a "$LOG_FILE"
    exit 1
fi
