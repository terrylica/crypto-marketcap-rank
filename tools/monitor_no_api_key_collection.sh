#!/bin/bash
# Monitor NO-API-KEY collection progress
# Usage: ./tools/monitor_no_api_key_collection.sh

LOG_FILE="logs/0001-coingecko-collection-20251120_195147.log"
MONITOR_LOG="logs/no-api-key-monitoring-$(date +%Y%m%d_%H%M%S).log"

echo "================================================" | tee -a "$MONITOR_LOG"
echo "NO-API-KEY Collection Monitoring" | tee -a "$MONITOR_LOG"
echo "Started: $(date)" | tee -a "$MONITOR_LOG"
echo "================================================" | tee -a "$MONITOR_LOG"
echo "" | tee -a "$MONITOR_LOG"

# Function to get stats
get_stats() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local successes=$(grep -c "✅.*records" "$LOG_FILE" 2>/dev/null || echo "0")
    local failures=$(grep -c "❌ Failed" "$LOG_FILE" 2>/dev/null || echo "0")
    local rate_limits=$(grep -c "RATE LIMIT" "$LOG_FILE" 2>/dev/null || echo "0")
    local total=$((successes + failures))
    local success_rate=0

    if [ $total -gt 0 ]; then
        success_rate=$(echo "scale=1; $successes * 100 / $total" | bc)
    fi

    local current=$(grep "\[.*/" "$LOG_FILE" 2>/dev/null | tail -1 | grep -oE '\[[0-9]+/[0-9]+\]' || echo "[0/500]")

    echo "[$timestamp] Progress: $current | Success: $successes/$total ($success_rate%) | Rate Limits: $rate_limits"
}

# Check if collection is running
if ! ps aux | grep "88218" | grep -v grep > /dev/null; then
    echo "❌ Collection process not found (PID 88218)" | tee -a "$MONITOR_LOG"
    echo "Checking if completed..." | tee -a "$MONITOR_LOG"

    if grep -q "Collection complete" "$LOG_FILE" 2>/dev/null; then
        echo "✅ Collection COMPLETED!" | tee -a "$MONITOR_LOG"
        echo "" | tee -a "$MONITOR_LOG"
        grep "COLLECTION SUMMARY" -A 20 "$LOG_FILE" | tee -a "$MONITOR_LOG"
    fi
    exit 0
fi

# Initial status
echo "Initial Status:" | tee -a "$MONITOR_LOG"
get_stats | tee -a "$MONITOR_LOG"
echo "" | tee -a "$MONITOR_LOG"

# Monitor loop
echo "Monitoring every 60 seconds (Ctrl+C to stop)..." | tee -a "$MONITOR_LOG"
echo "" | tee -a "$MONITOR_LOG"

while true; do
    sleep 60
    get_stats | tee -a "$MONITOR_LOG"

    # Check if completed
    if grep -q "Collection complete" "$LOG_FILE" 2>/dev/null; then
        echo "" | tee -a "$MONITOR_LOG"
        echo "================================================" | tee -a "$MONITOR_LOG"
        echo "✅ COLLECTION COMPLETED!" | tee -a "$MONITOR_LOG"
        echo "================================================" | tee -a "$MONITOR_LOG"
        echo "" | tee -a "$MONITOR_LOG"
        grep "COLLECTION SUMMARY" -A 20 "$LOG_FILE" | tee -a "$MONITOR_LOG"
        break
    fi

    # Check if process died
    if ! ps aux | grep "88218" | grep -v grep > /dev/null; then
        echo "" | tee -a "$MONITOR_LOG"
        echo "⚠️  Process terminated unexpectedly" | tee -a "$MONITOR_LOG"
        break
    fi
done

echo "" | tee -a "$MONITOR_LOG"
echo "Monitoring complete: $(date)" | tee -a "$MONITOR_LOG"
echo "Full log saved to: $MONITOR_LOG" | tee -a "$MONITOR_LOG"
