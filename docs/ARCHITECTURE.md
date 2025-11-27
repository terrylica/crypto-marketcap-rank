# Crypto Market Cap Rankings - System Architecture

**Last Validated**: 2025-11-25
**Validation Method**: Multi-agent DCTL (Dynamic Todo List Creation) audit
**Version**: v2.0.1

---

## System Overview

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                           SYSTEM ARCHITECTURE                             ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │                    GITHUB ACTIONS (Remote CI/CD)                    │  ║
║  │                                                                     │  ║
║  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │  ║
║  │  │  release.yml    │  │ daily-coll.yml  │  │ monitor-coll.yml│      │  ║
║  │  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤      │  ║
║  │  │ push main/beta  │  │ 6:00 AM UTC     │  │ every 6 hours   │      │  ║
║  │  │ • npm install   │  │ • uv run main.py│  │ • Check status  │      │  ║
║  │  │ • npm audit     │  │ • Build DuckDB  │  │ • Pushover alert│      │  ║
║  │  │ • sem-release   │  │ • gh release    │  │ • Doppler keys  │      │  ║
║  │  │       │         │  │       │         │  └─────────────────┘      │  ║
║  │  │       ▼         │  │       ▼         │                           │  ║
║  │  │  vX.Y.Z tags    │  │ daily-YYYY-MM-DD│   test-pushover.yml       │  ║
║  │  └─────────────────┘  └─────────────────┘   (manual testing)        │  ║
║  │                                                                     │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                    │                                      ║
║                          ┌─────────┴─────────┐                            ║
║                          │  GitHub Releases  │                            ║
║                          │  ├─ v2.0.1        │                            ║
║                          │  ├─ daily-11-25   │                            ║
║                          │  └─ daily-11-24   │                            ║
║                          └───────────────────┘                            ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                        LOCAL DEVELOPMENT (Earthly)                        ║
║                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  Earthfile (Docker via Colima)                                      │  ║
║  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │  ║
║  │  │+npm-install-test│  │ +release-test   │  │ +release-test-full  │  │  ║
║  │  │ Node 24 image   │  │ Plugins load    │  │ Full git context    │  │  ║
║  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  Local Python (uv run)                                              │  ║
║  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │  ║
║  │  │ pytest tests/   │  │ ruff check src/ │  │ npm run release:dry │  │  ║
║  │  │ 9 tests (0.01s) │  │ All checks pass │  │ All plugins load    │  │  ║
║  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                           DATA PIPELINE FLOW                              ║
║                                                                           ║
║  CoinGecko API (/coins/markets)                                           ║
║       │                                                                   ║
║       ▼  78 requests × 250 coins/page × 4s delay                          ║
║  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐         ║
║  │  COLLECT  │───▶│   BUILD   │───▶│ VALIDATE  │───▶│  RELEASE  │         ║
║  ├───────────┤    ├───────────┤    ├───────────┤    ├───────────┤         ║
║  │ raw/*.json│    │ *.duckdb  │    │ 5 rules:  │    │ gh release│         ║
║  │ 19,400+   │    │ *.parquet │    │ • schema  │    │ daily-*   │         ║
║  │ coins     │    │ (local)   │    │ • dupes   │    │ tags      │         ║
║  └───────────┘    └───────────┘    │ • nulls   │    └─────┬─────┘         ║
║                                    │ • range   │          │               ║
║                                    │ • values  │          ▼               ║
║                                    └───────────┘    ┌───────────┐         ║
║                                                     │ DuckDB    │         ║
║                                                     │ (Parquet  │         ║
║                                                     │ local)    │         ║
║                                                     └───────────┘         ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Repository Structure (Validated)

```
crypto-marketcap-rank/
├── .github/workflows/           # CI/CD automation (4 workflows)
│   ├── daily-collection.yml     # Daily collection + release (6:00 AM UTC)
│   ├── release.yml              # Semantic versioning (on push to main/beta)
│   ├── monitor-collection.yml   # Pushover notifications (every 6h)
│   └── test-pushover.yml        # Manual notification testing
│
├── src/                         # Production code
│   ├── collectors/              # CoinGecko API collector
│   │   └── coingecko_collector.py
│   ├── builders/                # Database builders
│   │   ├── base_builder.py      # Abstract base class
│   │   ├── build_duckdb.py      # DuckDB builder
│   │   └── build_parquet.py     # Parquet builder
│   ├── schemas/                 # PyArrow Schema V2 definition
│   │   └── crypto_rankings_schema.py
│   ├── validators/              # Validation layer (5 rules)
│   │   ├── schema_validator.py
│   │   └── data_validator.py
│   ├── utils/                   # Utilities
│   │   ├── rate_limiter.py
│   │   └── checkpoint_manager.py
│   ├── config/                  # Configuration (empty)
│   ├── __init__.py              # Package version
│   └── main.py                  # Entry point
│
├── tests/                       # Unit tests (9 tests)
│   ├── test_checkpoint_manager.py  # 5 tests
│   └── test_rate_limiter.py        # 4 tests
│
├── docs/                        # Documentation
│   ├── architecture/decisions/  # ADRs (MADR format)
│   ├── development/plan/        # Implementation plans
│   └── ARCHITECTURE.md          # This file
│
├── data/                        # Data storage (gitignored)
│   ├── raw/                     # Raw JSON from API
│   ├── processed/               # Built databases
│   ├── rankings/                # Rankings data
│   ├── coin_ids/                # Coin ID lists
│   └── analysis/                # Analysis outputs
│
├── schemas/                     # JSON schema definitions
│   └── crypto-rankings-v2.schema.json
│
├── scripts/                     # Standalone scripts
│   └── test_builders.py
│
├── tools/                       # Utility scripts (15 scripts)
│   ├── collect_coingecko.py
│   ├── merge_datasets.py
│   └── validate_all.sh
│
├── validation/                  # Validation infrastructure
│   ├── reports/
│   └── scripts/
│
├── logs/                        # Execution logs
├── research/                    # Historical research (archived)
│
├── Earthfile                    # Local CI/CD testing
├── .earthlyignore               # Earthly exclusions
├── .releaserc.yml               # semantic-release config
├── pyproject.toml               # Python project (>=3.12)
├── package.json                 # Node.js (>=22.14.0)
├── PROJECT_STATUS.md            # Project status
├── CHANGELOG.md                 # Auto-generated
└── README.md                    # Main documentation
```

---

## Schema V2 (100% Validated)

```
┌──────────────────────┬──────────────┬─────────────┬──────────┐
│       Column         │ PyArrow Type │  SQL Type   │ Nullable │
├──────────────────────┼──────────────┼─────────────┼──────────┤
│ date                 │ pa.date32()  │ DATE        │ NO       │
│ rank                 │ pa.int64()   │ BIGINT      │ NO       │
│ coin_id              │ pa.string()  │ VARCHAR     │ NO       │
├──────────────────────┼──────────────┼─────────────┼──────────┤
│ symbol               │ pa.string()  │ VARCHAR     │ YES      │
│ name                 │ pa.string()  │ VARCHAR     │ YES      │
│ market_cap           │ pa.float64() │ DOUBLE      │ YES      │
│ price                │ pa.float64() │ DOUBLE      │ YES      │
│ volume_24h           │ pa.float64() │ DOUBLE      │ YES      │
│ price_change_24h_pct │ pa.float64() │ DOUBLE      │ YES      │
└──────────────────────┴──────────────┴─────────────┴──────────┘

PyArrow Schema V2 (v2.0.0)
Source: src/schemas/crypto_rankings_schema.py
```

---

## GitHub Actions Workflows (Validated)

### 1. release.yml (Semantic Release)

```
Trigger: push to main/beta
Steps:  npm install → npm audit signatures → semantic-release
Output: vX.Y.Z tags + GitHub Release
```

### 2. daily-collection.yml (Data Collection)

```
Trigger: cron 6:00 AM UTC + workflow_dispatch
Steps:  uv run src/main.py → Build DuckDB/Parquet → gh release create
Output: daily-YYYY-MM-DD tag + DuckDB asset
Note:   Parquet built locally but NOT uploaded as release asset
```

### 3. monitor-collection.yml (Monitoring)

```
Trigger: workflow_run (after daily-collection) + cron every 6h
Steps:  Check status → Fetch Doppler secrets → Send Pushover notification
Output: HIGH priority alert on failure, silent on success
```

### 4. test-pushover.yml (Testing)

```
Trigger: workflow_dispatch only (manual)
Steps:  Test Pushover integration with different priority levels
Output: Test notifications to verify setup
```

---

## Release Strategy (Validated)

```
┌───────────────────────────────────────────────────────────────┐
│                     RELEASE TAG PATTERNS                      │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Semantic Versions           Daily Releases                   │
│  ─────────────────           ──────────────                   │
│  v2.0.1 (Latest)             daily-2025-11-25                 │
│  v2.0.0                      daily-2025-11-24                 │
│  v1.0.0                      daily-2025-11-23                 │
│                                                               │
│  Trigger: Conventional       Trigger: 6:00 AM UTC             │
│           commits on push              cron schedule          │
│                                                               │
│  Assets:  None (code only)   Assets: DuckDB database          │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│  NOTE: Parquet built locally but NOT in release assets        │
└───────────────────────────────────────────────────────────────┘
```

---

## Local Development (Validated)

### Requirements

| Tool    | Minimum Version | Current |
| ------- | --------------- | ------- |
| Python  | >=3.12          | 3.14.0  |
| Node    | >=22.14.0       | 25.2.1  |
| uv      | any             | 0.9.10  |
| Earthly | any             | 0.8.16  |

### Commands

```bash
# Run full pipeline
uv run src/main.py

# Run tests (9 tests, ~0.01s)
uv run pytest tests/ -v

# Run linter (all checks pass)
uv run ruff check src/ tests/

# Test CI locally with Earthly
earthly +npm-install-test      # Test npm install
earthly +release-test-full     # Full release workflow

# Semantic release dry-run
npm run release:dry
```

---

## Validation Summary

| Component | Accuracy | Status                        |
| --------- | -------- | ----------------------------- |
| Schema V2 | 100%     | ✅ Fully validated            |
| Workflows | 100%     | ✅ All 4 documented           |
| Releases  | 100%     | ✅ Patterns confirmed         |
| Structure | 100%     | ✅ All directories documented |
| Tooling   | 100%     | ✅ All commands work          |

**Validation Date**: 2025-11-25
**Method**: 5 parallel sub-agents using DCTL protocol
**Fixes Applied**: Deleted stale `latest` Draft release from GitHub

---

## API Usage

| Metric          | Value                                  |
| --------------- | -------------------------------------- |
| Daily API Calls | 78 (⌈19,411 ÷ 250⌉ per page limit)     |
| Monthly Usage   | ~2,340 calls (23% of 10,000 free tier) |
| Rate Limiting   | 4s delay with API key                  |
| Safety Margin   | 77% quota remaining                    |

---

## Architecture Decisions

| ADR      | Title                         | Status   |
| -------- | ----------------------------- | -------- |
| ADR-0002 | CI/CD Daily Rankings Database | Accepted |
| ADR-0003 | Schema V2 Migration           | Accepted |
| ADR-0008 | Repository Housekeeping       | Accepted |

---

**Document Status**: ✅ Validated and accurate as of 2025-11-25
