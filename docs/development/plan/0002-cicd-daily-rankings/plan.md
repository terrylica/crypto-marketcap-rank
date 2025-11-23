# Implementation Plan: CI/CD Daily Cryptocurrency Rankings Database

**adr-id**: 0002
**Status**: In Progress
**Created**: 2025-11-21
**Authors**: AI Assistant
**Reviewers**: Terry Li

---

## Context

### Background

The crypto-marketcap-rank project currently has manual collection tools but lacks automation for daily data collection and distribution. Research has validated:

- **19,411 active cryptocurrencies** tracked by CoinGecko
- **78 API calls required** to fetch all coins (empirically validated: ⌈19,411 ÷ 250⌉)
- **23% of monthly quota** usage (2,340 of 10,000 calls) - sustainable indefinitely
- **Multiple format requirements**: DuckDB (public queries), Parquet (ClickHouse import), CSV (compatibility)

### Problem Statement

Need automated system that:

1. Collects all 19,411 CoinGecko coins daily without manual intervention
2. Builds three database formats (DuckDB, Parquet, CSV) from collected data
3. Distributes via GitHub Releases with stable download URLs
4. Validates data quality before each release
5. Operates within free tier constraints (GitHub Actions + CoinGecko API)

### Empirical Evidence

Sub-agent research validated:

- **Pagination formula**: `API_Calls = ⌈Total_Coins ÷ 250⌉` (6 independent sources)
- **Per-page hard limit**: 250 coins (official docs + Stack Overflow tests + production code)
- **Rate limiting**: 30 calls/min free tier, 10,000 calls/month
- **Proven pattern**: hikeratlas/qrank uses GitHub Releases for 307 MB SQLite database

---

## Goals

### Primary Goals

1. **Availability**: Daily automated collection runs successfully >95% of time
2. **Correctness**: Zero data quality issues (duplicates, nulls, rank gaps)
3. **Observability**: All failures logged, API quota tracked, validation reports generated
4. **Maintainability**: Standard tooling (uv, pytest), conventional commits, auto-changelog

### Non-Goals

- **Performance optimization**: Collection speed not critical (15-20 min acceptable)
- **Security hardening**: Public data, no sensitive information
- **Backward compatibility**: No legacy code support needed
- **Historical backfill**: Kaggle integration deferred (start fresh from today)

---

## Design

### High-Level Architecture

```
┌─────────────────┐
│  GitHub Actions │  Daily Cron 6:00 AM UTC
│   Workflow      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Collection    │  CoinGecko API: 78 calls
│   (Python)      │  → raw/YYYY-MM-DD.json
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Builders       │  DuckDB + Parquet + CSV
│  (parallel)     │  → releases/*.{duckdb,parquet,csv.gz}
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validation     │  Quality checks
│  (pytest)       │  → pass/fail
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Release        │  GitHub Releases
│  (gh CLI)       │  → "latest" tag update
└─────────────────┘
```

### Detailed Design

#### Component 1: Collection System

**File**: `src/collectors/coingecko_collector.py`

**Responsibilities**:

- Fetch `/coins/markets` endpoint with pagination
- Respect rate limits (4s delay with API key, 20s without)
- Save raw responses to `data/raw/YYYY-MM-DD.json`
- Checkpoint progress (GitHub Actions cache)
- Handle errors (retry 3x, then fail)

**Interface**:

```python
class CoinGeckoCollector:
    def collect_all_coins(self, date: str) -> Path:
        """Collect all 19,411 coins for specific date.

        Returns: Path to raw JSON file
        Raises: CollectionError if API fails after retries
        """
```

**Empirical Logic**:

```python
COINS_PER_PAGE = 250  # CoinGecko hard limit (validated)
TOTAL_COINS = 19_411  # Current count
PAGES_REQUIRED = math.ceil(TOTAL_COINS / COINS_PER_PAGE)  # 78
```

#### Component 2: Database Builders

**Files**: `src/builders/{build_duckdb,build_parquet,build_csv}.py`

**Shared Interface**:

```python
class DatabaseBuilder(ABC):
    @abstractmethod
    def build(self, raw_data: Path, output_dir: Path) -> Path:
        """Build database from raw JSON."""
```

**Schema** (all formats):

```
- date: DATE
- rank: INT (1 to 19,411)
- coin_id: VARCHAR (CoinGecko ID)
- symbol: VARCHAR (ticker)
- name: VARCHAR
- market_cap: DOUBLE
- price: DOUBLE
- volume_24h: DOUBLE
```

**DuckDB Builder**:

- Create indexed, compressed database
- Indexes: (date, rank), (coin_id), (symbol)
- Expected size: ~200 MB/year

**Parquet Builder**:

- Date partitioning: `year=YYYY/month=MM/day=DD/`
- zstd compression level 3
- Expected size: ~100 MB/year

**CSV Builder**:

- Simple CSV + gzip compression
- Expected size: ~50 MB/year

#### Component 3: Validation System

**File**: `src/utils/validator.py`

**Checks**:

1. **Completeness**: Expected ~19,411 rows per date
2. **Uniqueness**: No duplicate (date, coin_id) pairs
3. **Sequence**: Ranks are 1, 2, 3, ..., N (no gaps)
4. **Sorting**: Ranks ordered by market_cap descending
5. **Nullability**: No nulls in required fields
6. **Reasonability**: Market cap > 0, price > 0, volume ≥ 0

**Interface**:

```python
def validate_dataset(df: pd.DataFrame, date: str) -> ValidationReport:
    """Run all quality checks.

    Raises: ValidationError if any check fails
    """
```

#### Component 4: Release Automation

**File**: `scripts/publish_release.sh`

**Pattern** (from hikeratlas/qrank):

```bash
# Atomic release update
1. Delete existing "latest" assets
2. Upload new artifacts (DuckDB, Parquet, CSV)
3. Update release notes with collection metadata
```

**Stable Download URLs**:

```
https://github.com/USER/REPO/releases/download/latest/crypto_rankings.duckdb
https://github.com/USER/REPO/releases/download/latest/crypto_rankings.parquet.tar.zst
https://github.com/USER/REPO/releases/download/latest/crypto_rankings.csv.gz
```

### Project Structure

```
crypto-marketcap-rank/
├── .github/workflows/
│   ├── daily-collection.yml        # Main workflow (cron + manual)
│   ├── monthly-archive.yml         # Create versioned releases
│   └── api-validation.yml          # Weekly empirical tests
│
├── src/
│   ├── collectors/
│   │   └── coingecko_collector.py  # API collection
│   ├── builders/
│   │   ├── build_duckdb.py
│   │   ├── build_parquet.py
│   │   └── build_csv.py
│   ├── utils/
│   │   ├── checkpoint_manager.py   # State persistence
│   │   ├── rate_limiter.py         # API quota tracking
│   │   └── validator.py            # Data quality
│   └── config/
│       └── settings.py             # Configuration
│
├── data/                           # Gitignored
│   ├── raw/                        # Raw API responses
│   ├── processed/                  # Intermediate data
│   └── releases/                   # Built artifacts
│
├── scripts/
│   ├── publish_release.sh          # GitHub Release automation
│   └── validate_data.py            # Validation runner
│
├── tests/
│   ├── test_collectors.py
│   ├── test_builders.py
│   └── test_validators.py
│
├── docs/
│   ├── architecture/decisions/
│   │   └── 0002-cicd-daily-rankings.md  # This ADR
│   └── development/plan/
│       └── 0002-cicd-daily-rankings/
│           └── plan.md             # This file
│
├── logs/                           # Execution logs
├── pyproject.toml                  # Dependencies
├── .gitignore                      # Exclude data/
└── README.md                       # User-facing docs
```

---

## Task List

### Phase 1: Project Setup (4-6 hours)

- [x] **TASK-001**: Create ADR-0002 in MADR format
- [x] **TASK-002**: Create implementation plan (this document)
- [ ] **TASK-003**: Create directory structure (src/, data/, scripts/, logs/)
- [ ] **TASK-004**: Update .gitignore (exclude data/, include logs/)
- [ ] **TASK-005**: Setup pyproject.toml with dependencies (duckdb, pyarrow, requests, pytest)
- [ ] **TASK-006**: Create catalog-info.yaml (optional service metadata)

### Phase 2: Core Collection System (6-8 hours)

- [ ] **TASK-007**: Implement CoinGeckoCollector class with pagination
- [ ] **TASK-008**: Implement RateLimiter (30 calls/min tracking)
- [ ] **TASK-009**: Implement CheckpointManager (GitHub Actions cache integration)
- [ ] **TASK-010**: Add error handling (raise + propagate, no silent failures)
- [ ] **TASK-011**: Add progress logging (status every 15-60s for ops >1min)
- [ ] **TASK-012**: Write unit tests (mock API responses)
- [ ] **TASK-013**: Validate: Run `uv run src/collectors/coingecko_collector.py` → auto-fix errors

### Phase 3: Database Builders (6-8 hours)

- [ ] **TASK-014**: Implement DuckDB builder (indexed, compressed)
- [ ] **TASK-015**: Implement Parquet builder (date partitioning, zstd compression)
- [ ] **TASK-016**: Implement CSV builder (gzip compression)
- [ ] **TASK-017**: Shared schema validation across all builders
- [ ] **TASK-018**: Write unit tests (verify schemas, compression ratios)
- [ ] **TASK-019**: Validate: Build sample databases → check file sizes → auto-fix errors

### Phase 4: Validation System (4-6 hours)

- [ ] **TASK-020**: Implement Validator class with 6 quality checks
- [ ] **TASK-021**: Implement ValidationReport dataclass
- [ ] **TASK-022**: Add anomaly detection (rank jumps >1000, market cap >1000% change)
- [ ] **TASK-023**: Write unit tests (edge cases: duplicates, nulls, gaps)
- [ ] **TASK-024**: Validate: Run against existing data/rankings/ → surface errors → auto-fix

### Phase 5: GitHub Actions Workflows (8-10 hours)

- [ ] **TASK-025**: Create daily-collection.yml (cron 6:00 AM UTC + manual trigger)
- [ ] **TASK-026**: Implement cache strategy (checkpoint + raw data)
- [ ] **TASK-027**: Add validation step (fail pipeline if checks fail)
- [ ] **TASK-028**: Implement release step (atomic "latest" update)
- [ ] **TASK-029**: Add Slack notifications (optional, on failure)
- [ ] **TASK-030**: Create monthly-archive.yml (versioned releases)
- [ ] **TASK-031**: Create api-validation.yml (weekly empirical tests)
- [ ] **TASK-032**: Validate: Manual workflow trigger → check logs → auto-fix errors

### Phase 6: Release Automation (2-3 hours)

- [ ] **TASK-033**: Create publish_release.sh script
- [ ] **TASK-034**: Implement asset deletion + upload (atomic operation)
- [ ] **TASK-035**: Generate release notes (collection date, coin count, file sizes)
- [ ] **TASK-036**: Test release workflow locally with `gh` CLI
- [ ] **TASK-037**: Validate: Create test release → verify download URLs → auto-fix errors

### Phase 7: Semantic Release Setup (2-3 hours)

- [ ] **TASK-038**: Invoke semantic-release skill (setup with GH token)
- [ ] **TASK-039**: Configure conventional commits (feat/fix/docs/chore)
- [ ] **TASK-040**: Setup changelog auto-generation
- [ ] **TASK-041**: Test: Make dummy commit → verify tag/release → auto-fix errors

### Phase 8: Documentation (4-6 hours)

- [ ] **TASK-042**: Update README.md (quick start, download examples)
- [ ] **TASK-043**: Create USAGE_GUIDE.md (DuckDB/Parquet/CSV query examples)
- [ ] **TASK-044**: Create API_USAGE.md (CoinGecko attribution, rate limits)
- [ ] **TASK-045**: Document ClickHouse import workflow (Parquet → ClickHouse)
- [ ] **TASK-046**: Add query examples (SQL, Python, R)
- [ ] **TASK-047**: Update CLAUDE.md with new structure

### Phase 9: Testing & Validation (4-6 hours)

- [ ] **TASK-048**: Run full pytest suite → surface all errors → auto-fix
- [ ] **TASK-049**: Manual test: Trigger daily workflow → monitor logs
- [ ] **TASK-050**: Validate first release artifacts (download + query)
- [ ] **TASK-051**: Week 1 monitoring: Check daily runs → iterate on failures
- [ ] **TASK-052**: Validate SLO targets (availability >95%, correctness 100%)

### Phase 10: PyPI Publishing (1-2 hours) [OPTIONAL]

- [ ] **TASK-053**: Invoke pypi-doppler skill (access PYPI_TOKEN from Doppler)
- [ ] **TASK-054**: Package src/ as installable library (if needed)
- [ ] **TASK-055**: Test: `uv publish` with Doppler credentials

---

## Timeline

### Week 1: Foundation (20-24 hours)

- **Days 1-2**: Phases 1-2 (Setup + Collection System)
- **Days 3-4**: Phases 3-4 (Builders + Validation)
- **Day 5**: Phase 5 (GitHub Actions - start)

### Week 2: Integration (10-12 hours)

- **Days 6-7**: Phase 5 (GitHub Actions - complete) + Phase 6 (Release)
- **Days 8-9**: Phase 7 (Semantic Release) + Phase 8 (Documentation)
- **Day 10**: Phase 9 (Testing - start)

### Week 3: Launch (6-8 hours)

- **Days 11-12**: Phase 9 (Testing - complete)
- **Day 13**: First production run
- **Days 14-15**: Monitoring + iteration

**Total Estimated Time**: 36-44 hours over 3 weeks

---

## Metrics and Success Criteria

### Availability SLO

**Target**: >95% daily collection success rate

**Measurement**:

```python
# logs/0002-cicd-daily-rankings-YYYYMMDD_HHMMSS.log
success_rate = successful_runs / total_runs * 100
```

**Alerting**: Slack notification if failure

### Correctness SLO

**Target**: Zero data quality issues

**Checks** (auto-fail pipeline if violated):

1. Row count ≈ 19,411 (±100 tolerance for market changes)
2. No duplicate (date, coin_id) pairs
3. Ranks sequential: 1, 2, 3, ..., N
4. Market caps sorted descending
5. No nulls in required fields
6. Anomaly detection: No rank jumps >1000

### Observability SLO

**Target**: All failures logged with context

**Logs**:

- **Collection**: API calls, rate limit status, checkpoint state
- **Builders**: Input/output sizes, compression ratios
- **Validation**: Check results, anomalies detected
- **Release**: Upload status, artifact URLs

**Format**: `logs/0002-cicd-daily-rankings-YYYYMMDD_HHMMSS.log`

### Maintainability SLO

**Target**: Documentation current, changelog automated

**Requirements**:

- ADR-0002 updated with changes
- This plan updated with task status
- Conventional commits enforced
- Changelog auto-generated (semantic-release)

---

## Risks and Mitigation

### Risk 1: CoinGecko API Rate Limit Exceeded

**Probability**: Low (using 23% of quota)
**Impact**: High (daily collection fails)

**Mitigation**:

- 77% buffer for errors/retries
- Rate limiter tracks quota usage
- Checkpoint allows resume from failure
- Fallback: Reduce to top 5K coins if needed

### Risk 2: GitHub Actions Downtime

**Probability**: Low (<1% historically)
**Impact**: Medium (delayed release)

**Mitigation**:

- Manual collection script available
- Checkpoint persists state
- Can run locally if needed

### Risk 3: Data Quality Issues

**Probability**: Medium (API changes, market anomalies)
**Impact**: High (corrupted releases)

**Mitigation**:

- Validation before every release (fail pipeline if issues found)
- Manual review for first 7 days
- Rollback to previous release if needed

### Risk 4: Storage Growth

**Probability**: High (inevitable with daily data)
**Impact**: Low (200 MB/year manageable)

**Mitigation**:

- Compression keeps sizes small
- Monthly archives (not daily tags)
- .gitignore excludes data from repo

---

## Alternatives Considered

### Alternative 1: DuckDB Only (No Parquet/CSV)

**Rejected**: Doesn't serve ClickHouse import use case, limits flexibility

### Alternative 2: Parquet Only (No DuckDB)

**Rejected**: Less accessible to non-technical users, requires extraction

### Alternative 3: Kaggle Historical Integration

**Deferred**: Adds complexity (coin ID mapping CMC ↔ CoinGecko), can backfill later if needed

### Alternative 4: Top 5K Coins (Not All 19,411)

**Rejected**: Empirical research showed 78 calls sustainable (23% quota), complete coverage achievable

---

## References

- **ADR**: `docs/architecture/decisions/0002-cicd-daily-rankings.md`
- **Empirical Research**: Sub-agent reports (database comparison, API validation, collection strategy)
- **CoinGecko API Docs**: https://docs.coingecko.com/reference/coins-markets
- **DuckDB Docs**: https://duckdb.org/docs/
- **Proven Pattern**: hikeratlas/qrank (GitHub Releases for SQLite)

---

## Changelog

- **2025-11-21 09:00**: Plan created, Phases 1-10 defined
- **2025-11-21 09:30**: Task 001-002 completed (ADR + Plan created)
- **2025-11-21 17:00**: Phase 1 complete (directory structure, configs)
- **2025-11-21 17:01**: Task 007 completed (CoinGeckoCollector implemented, validated)

---

## Status Tracking

**Last Updated**: 2025-11-21 18:38 PST
**Current Phase**: Phase 3 Complete, Phase 5 Running
**Completed Tasks**: 19/55 (35%)
**Tasks Completed**:

- Phase 1: TASK-001 to TASK-006 (ADR, Plan, Setup) ✅
- Phase 2: TASK-007 to TASK-009, TASK-012 (Collector, RateLimiter, CheckpointManager, Tests) ✅
- Phase 3: TASK-014 to TASK-019 (DuckDB, Parquet, CSV Builders + Validation) ✅
  - Fixed: Parquet builder date type conversion (pa.string() instead of pa.date32())
  - Validated: All 3 builders with 500 coins real data
  - File sizes: DuckDB 1.26 MB, Parquet 0.03 MB, CSV.gz 0.02 MB
  - Created: scripts/test_builders.py validation script
- Phase 5: GitHub Actions workflow running (Run ID: 19588848366)
  - Status: Collection step in progress (~8 min elapsed)
  - Expected: 15-20 min total for 19,411 coins

**Blockers**: None
**Status**: On track, GitHub Actions running first production test
**Next Action**: Monitor workflow completion, then proceed to Phase 6 (Release Automation)
