# ADR-0009: Documentation Rectification

## Status

Accepted

## Date

2025-11-25

## Context and Problem Statement

A comprehensive 9-agent DCTL (Dynamic Todo List Creation) audit identified documentation inconsistencies, missing files, and cross-reference discrepancies across the repository. These issues impact correctness (inaccurate claims), maintainability (stale information), and observability (incomplete workflow documentation).

### Audit Findings Summary

| Category         | Score    | Critical Issues                |
| ---------------- | -------- | ------------------------------ |
| Doc Inventory    | 61 files | Missing LICENSE                |
| ARCHITECTURE.md  | 95%      | Tools count inaccurate         |
| README.md        | 8/10     | Missing LICENSE file reference |
| Schema Docs      | 98%      | Symbol format inconsistency    |
| ADR Compliance   | 9.7/10   | Plan YAML status mismatch      |
| Cross-References | 85%      | Version discrepancy            |
| Code Comments    | 93%      | Minor gaps in CLI entry points |

### Key Issues Identified

1. **Legal**: Missing LICENSE file (referenced but non-existent)
2. **Accuracy**: Symbol format inconsistency (lowercase vs uppercase)
3. **Consistency**: Version discrepancy (v2.0.0 vs v2.0.1)
4. **Completeness**: Missing workflow documentation in README

## Decision Drivers

- **Correctness**: Documentation must match source of truth (code)
- **Maintainability**: Use dynamic references to prevent staleness
- **Observability**: All CI/CD workflows must be documented
- **Availability**: Legal compliance requires LICENSE file

## Considered Options

1. **Comprehensive Fix** - Address all P0-P3 issues
2. **Critical Only** - Address only P0 issues
3. **Incremental** - Fix issues as encountered

## Decision Outcome

**Chosen Option**: Comprehensive Fix with user-guided scope refinement

- Fix all existing documentation issues (P0-P3)
- Use dynamic latest release API for example URLs
- Skip Plan 0001 modifications (per user decision)
- Do not create new documentation files (INDEX.md, CONTRIBUTING.md)

## Implementation

### Files Modified

| File                                     | Changes                                      | Priority |
| ---------------------------------------- | -------------------------------------------- | -------- |
| `LICENSE`                                | CREATE with MIT text                         | P0       |
| `PROJECT_STATUS.md`                      | Version v2.0.0→v2.0.1                        | P0       |
| `README.md`                              | Symbol format, ADR links, Node.js, workflows | P0-P2    |
| `schemas/crypto-rankings-v2.schema.json` | Symbol format lowercase                      | P0       |
| `docs/ARCHITECTURE.md`                   | Tools count 17→15                            | P1       |
| `docs/development/plan/0008-*/plan.md`   | YAML status→complete                         | P1       |
| `src/main.py`                            | Add Returns docstring                        | P3       |
| `src/collectors/coingecko_collector.py`  | Add Returns docstring                        | P3       |
| `.releaserc.yml`                         | Add inline comments                          | P3       |

### Validation Criteria

- [ ] LICENSE file exists and is valid MIT
- [ ] All version numbers consistent (v2.0.1)
- [ ] Symbol examples all lowercase (btc)
- [ ] Tools count = 15
- [ ] All 4 ADRs linked in README
- [ ] Plan 0008 YAML status = complete
- [ ] Node.js >=22.14.0 in README
- [ ] All 4 workflows documented
- [ ] CLI functions have Returns docstrings

## Consequences

### Positive

- Legal compliance restored (LICENSE file)
- Documentation accuracy improved to ~99%
- Cross-reference consistency achieved
- Maintainable dynamic URL references

### Negative

- One-time effort required (~25 minutes)

### Neutral

- Plan 0001 remains in current state (user decision)
- No new documentation files created

## Related Decisions

- [ADR-0008: Repository Housekeeping](0008-repository-housekeeping.md) - Previous cleanup effort
- [ADR-0003: Schema V2 Migration](0003-schema-v2-migration.md) - Source of truth for schema

## References

- Multi-agent DCTL audit (9 sub-agents, 2025-11-25)
- Plan file: `docs/development/plan/0009-documentation-rectification/plan.md`
