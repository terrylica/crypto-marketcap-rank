# Risk Analysis & Mitigation Strategies

**Date**: November 20, 2025
**Focus**: Implementing all-coins historical market cap collection
**Total Coins**: 13,532

---

## Risk Categories

### 1. API RATE LIMIT RISKS

#### Risk 1.1: Monthly Budget Overrun

**Severity**: MEDIUM
**Probability**: LOW (with recommended strategy)

**Description**: Free tier has 20,000 calls/month. If implementation is inefficient, could exceed budget.

**Our Strategy**:

- Daily snapshot via `/v1/tickers`: 55 calls/day × 30 = 1,650 calls/month
- Headroom: 20,000 - 1,650 = 18,350 calls (92% safety margin)

**Mitigation**:

- Monitor API call count daily
- Set alert at 15,000 calls/month (75% of budget)
- Implement exponential backoff retry logic
- Cache responses when possible

**Risk Score After Mitigation**: LOW (2%)

---

#### Risk 1.2: Daily Burst Limit

**Severity**: LOW
**Probability**: LOW

**Description**: Free tier allows ~650 calls/day. Daily snapshot uses 55 calls.

**Headroom**: 650 - 55 = 595 calls/day (91% remaining)

**Can safely add**:

- 11 additional global snapshots per day
- 5 backfill operations per day
- Other monitoring calls

**Risk Score After Mitigation**: NEGLIGIBLE (1%)

---

#### Risk 1.3: Real-time Rate Limits

**Severity**: LOW
**Probability**: MEDIUM

**Description**: CoinPaprika has per-second rate limits (20 ticks/second) not officially documented.

**Mitigation**:

- Space requests 50ms apart (20 requests/second → 50ms per request)
- Daily snapshot takes 55 × 0.1s = 5.5 seconds minimum
- Add 2-second buffer between request batches
- Implement circuit breaker for 429 errors

**Implementation**:

```python
import time
requests_per_batch = 10
batch_delay_seconds = 1.0
request_delay_seconds = 0.05

for batch in paginated_requests:
    for request in batch:
        make_request()
        time.sleep(request_delay_seconds)
    time.sleep(batch_delay_seconds)
```

**Risk Score After Mitigation**: LOW (5%)

---

### 2. DATA QUALITY RISKS

#### Risk 2.1: Missing Coins

**Severity**: MEDIUM
**Probability**: LOW

**Description**: Pagination might miss coins or duplicate them across pages.

**Monitoring**:

- Track coin IDs per snapshot
- Alert if coin count < 13,500
- Compare to previous day's count

**Mitigation**:

- Verify offset calculation: `offset = page * 250`
- Confirm total from API response (if available)
- Perform monthly audit of coin coverage

**Risk Score After Mitigation**: LOW (3%)

---

#### Risk 2.2: Null or Invalid Market Cap Values

**Severity**: LOW
**Probability**: MEDIUM

**Description**: Some coins might have null market cap (new coins, delisted coins).

**Expected Frequency**: ~1-2% of coins monthly

**Mitigation**:

- Validate market_cap > 0 before storing
- Log coins with null/missing market cap
- Track invalid record count per snapshot
- Alert if > 5% invalid records

**Implementation**:

```python
if record.get("quotes", {}).get("USD", {}).get("market_cap") is None:
    log_invalid_record(record_id)
    skip_record()
else:
    store_record()
```

**Risk Score After Mitigation**: LOW (2%)

---

#### Risk 2.3: Timestamp Drift

**Severity**: LOW
**Probability**: LOW

**Description**: Coins' last_updated times might be stale (> 5 minutes old).

**Mitigation**:

- Add collection timestamp (server time) to each snapshot
- Track max age per snapshot
- Alert if > 30% of coins are > 10 minutes stale
- Retry snapshot if too many stale records

**Risk Score After Mitigation**: LOW (3%)

---

### 3. STORAGE & DATABASE RISKS

#### Risk 3.1: Storage Saturation

**Severity**: LOW
**Probability**: LOW

**Description**: Annual storage grows ~0.92 GB/year. Could eventually fill disk.

**Mitigation**:

- Monitor disk usage monthly
- Warn at 50% capacity
- Implement archival strategy at 80% capacity
- Plan for expansion every 10 years (9.2 GB total)

**Archival Strategy**:

- Compress old data with gzip (10x compression to 90 MB/year)
- Move to cold storage after 2 years
- Keep hot storage for recent 2 years only

**Risk Score After Mitigation**: LOW (1%)

---

#### Risk 3.2: Data Corruption

**Severity**: MEDIUM
**Probability**: LOW

**Description**: JSONL file corruption could lose data.

**Mitigation**:

- Use append-only JSONL format (line-based)
- One corrupt line ≠ entire dataset lost
- Weekly checksums of data files
- Monthly backup to separate location
- Schema validation on read

**Implementation**:

- Store complete coin snapshots, one per line
- Validate JSON parsing with try/catch
- Log failed lines separately

**Risk Score After Mitigation**: LOW (2%)

---

#### Risk 3.3: Timezone Issues

**Severity**: LOW
**Probability**: LOW

**Description**: Inconsistent timezone handling could create gaps.

**Mitigation**:

- Always use UTC timestamps
- Specify timezone in all code comments
- Parse ISO 8601 timestamps from API
- Store all timestamps as Unix seconds + ISO string

**Risk Score After Mitigation**: NEGLIGIBLE (1%)

---

### 4. IMPLEMENTATION RISKS

#### Risk 4.1: Script Failure / Uptime

**Severity**: MEDIUM
**Probability**: MEDIUM

**Description**: Cron job might fail, skip days, or hang.

**Mitigation**:

- Run daily collection at fixed time (e.g., midnight UTC)
- Monitor for missing daily files
- Implement watchdog timer (exit after 5 minutes)
- Log all executions to syslog
- Implement auto-retry on failure

**Implementation**:

```bash
# Crontab entry
0 0 * * * cd /path/to/project && timeout 300 python3 collect.py 2>&1 | logger -t marketcap
```

**Alerting**:

- Daily email if file not created
- Alert if > 1 day gap
- Check file size is reasonable (> 100 KB for 13K coins)

**Risk Score After Mitigation**: MEDIUM (15%)

---

#### Risk 4.2: API Endpoint Changes

**Severity**: LOW
**Probability**: LOW

**Description**: CoinPaprika might change API structure (major version bump).

**Mitigation**:

- Monitor API status page weekly
- Subscribe to CoinPaprika status updates
- Implement version detection in API responses
- Maintain backward compatibility layer
- Have upgrade plan ready (v1 → v2)

**Risk Score After Mitigation**: LOW (5%)

---

#### Risk 4.3: Cost Escalation (if choosing paid tier)

**Severity**: LOW
**Probability**: MEDIUM

**Description**: CoinPaprika raises API prices.

**Mitigation**:

- Recommended strategy uses FREE tier (no price exposure)
- If using Starter plan ($40/month), monitor cost
- Build ability to switch providers
- Keep API calls minimal (55/day is very low)

**Risk Score After Mitigation**: LOW (2%)

---

### 5. OPERATIONAL RISKS

#### Risk 5.1: Monitoring Blindness

**Severity**: MEDIUM
**Probability**: MEDIUM

**Description**: Collection runs silently for weeks without errors, then fails.

**Mitigation**:

- Log every snapshot attempt
- Alert on 2+ consecutive failures
- Weekly status report (count of files, size, coin coverage)
- Dashboard showing last collection time
- Alerting on gaps > 1 day

**Monitoring Checklist**:

- [ ] Daily file created with < 1 hour age
- [ ] File size 300 KB - 500 KB (expected range)
- [ ] Coin count in file = 13,532 ± 50
- [ ] Timestamps valid (within 1 hour of collection)

**Risk Score After Mitigation**: LOW (5%)

---

#### Risk 5.2: No Historical Baseline on Day 1

**Severity**: LOW
**Probability**: HIGH

**Description**: Starting with empty database means no historical data for first year.

**Mitigation**:

- Use optional Starter plan for Month 1 ($40 one-time)
- Backfills 30 days of history in first month
- Then downgrade to free tier for ongoing
- Total cost: $40 (one-time)

**Alternative**: Accept that history builds from today forward

**Risk Score After Mitigation**: LOW (3%)

---

#### Risk 5.3: Skill Dependencies

**Severity**: LOW
**Probability**: LOW

**Description**: Knowledge concentrated in one person.

**Mitigation**:

- Document all procedures
- Create runbook for troubleshooting
- Script should be self-documenting
- Quarterly review/test of disaster recovery

**Risk Score After Mitigation**: LOW (2%)

---

## Risk Summary Matrix

| Risk                   | Severity | Probability | After Mitigation | Status     |
| ---------------------- | -------- | ----------- | ---------------- | ---------- |
| Monthly budget overrun | M        | L           | 2%               | ACCEPTABLE |
| Daily burst limit      | L        | L           | 1%               | ACCEPTABLE |
| Real-time rate limits  | L        | M           | 5%               | ACCEPTABLE |
| Missing coins          | M        | L           | 3%               | ACCEPTABLE |
| Invalid market cap     | L        | M           | 2%               | ACCEPTABLE |
| Timestamp drift        | L        | L           | 3%               | ACCEPTABLE |
| Storage saturation     | L        | L           | 1%               | ACCEPTABLE |
| Data corruption        | M        | L           | 2%               | ACCEPTABLE |
| Timezone issues        | L        | L           | 1%               | ACCEPTABLE |
| Script failure/uptime  | M        | M           | 15%              | MONITOR    |
| API changes            | L        | L           | 5%               | ACCEPTABLE |
| Cost escalation        | L        | M           | 2%               | ACCEPTABLE |
| Monitoring blindness   | M        | M           | 5%               | MONITOR    |
| No historical baseline | L        | H           | 3%               | ACCEPTABLE |
| Skill dependencies     | L        | L           | 2%               | ACCEPTABLE |

**Critical Risks**: SCRIPT FAILURE & MONITORING BLINDNESS (both 15% and 5%)

**Mitigation Required**: Implement comprehensive logging, alerting, and uptime monitoring

---

## Implementation Checklist

### Phase 1: Setup (Week 1)

- [ ] Create directory structure
- [ ] Write daily collection script
- [ ] Test with 10 sample coins
- [ ] Set up logging
- [ ] Create JSONL storage file
- [ ] Test data parsing and validation

### Phase 2: Monitoring (Week 2)

- [ ] Set up cron job
- [ ] Create monitoring script
- [ ] Set up alerting
- [ ] Create status dashboard
- [ ] Test failure scenarios
- [ ] Document troubleshooting

### Phase 3: Backfill (Week 3, Optional)

- [ ] Sign up for Starter plan
- [ ] Download previous 30 days for all coins
- [ ] Merge with ongoing collection
- [ ] Downgrade to free tier
- [ ] Verify data consistency

### Phase 4: Validation (Week 4)

- [ ] Run 7 consecutive days
- [ ] Verify all coin counts
- [ ] Check timestamp validity
- [ ] Audit sample coins
- [ ] Test archival strategy
- [ ] Document final setup

---

## Conclusion

**Overall Risk Level**: LOW (with recommended mitigations)

**Critical Paths**:

1. Implement comprehensive logging and alerting (HIGHEST PRIORITY)
2. Set up daily monitoring checks (HIGH PRIORITY)
3. Document runbook for common failures (HIGH PRIORITY)

**Go/No-Go Decision**: READY TO PROCEED (with Phase 2 monitoring in place)
