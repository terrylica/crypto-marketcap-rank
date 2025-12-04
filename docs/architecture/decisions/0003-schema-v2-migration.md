# ADR-0003: Schema V2 Migration - PyArrow Native Types

**Status**: Accepted
**Date**: 2025-11-23
**Authors**: AI Assistant
**Deciders**: Terry Li
**Related**: ADR-0002 (CI/CD Daily Rankings Database)

## Context and Problem Statement

Current database builders (DuckDB, Parquet, CSV) have schema inconsistencies that create type coercion challenges and reduce data integrity. Specifically:

- **Date representation**: DuckDB uses native DATE type, Parquet uses STRING, CSV uses STRING
- **Rank precision**: DuckDB uses INTEGER (64-bit), Parquet uses INT32 (32-bit)
- **Validation coverage**: DuckDB has comprehensive validation, Parquet/CSV have minimal checks
- **Type safety**: CoinGecko API returns mixed types (int/float/string) causing PyArrow type errors

**Key Evidence**:

- Parquet build failures with "object of type <class 'str'> cannot be converted to int"
- Schema defined separately in each builder → drift over time
- CSV validation only spot-checks first 10 rows

## Decision Drivers

- **Correctness**: Strict type safety prevents silent data corruption
- **Maintainability**: Single source of truth for schema (DRY principle)
- **Observability**: Comprehensive validation catches data quality issues early
- **Availability**: Future-proof schema using Apache Arrow ecosystem (10-year horizon)

## Considered Options

### Option 1: PyArrow Native Schema + Parquet-Only (SELECTED)

- **Description**: Define schema once in PyArrow, generate DuckDB/Parquet from it, deprecate CSV
- **Pros**: Single source of truth, Apache Arrow 10-year future-proof, zero-copy DuckDB interop
- **Cons**: Breaking change (STRING → DATE), no CSV output
- **Evidence**: Industry trend (DuckDB 2024: Parquet 2x faster, 5x smaller than CSV)

### Option 2: JSON Schema + Code Generation

- **Description**: Define schema in JSON Schema, auto-generate Python/PyArrow/SQL
- **Pros**: Human-readable spec, validation tooling, API documentation
- **Cons**: One-way generation, not native to data tools, extra complexity

### Option 3: Keep Status Quo + Add Validation

- **Description**: Fix type coercion bugs, add validation, keep heterogeneous schemas
- **Pros**: No breaking changes, backward compatible
- **Cons**: Schema drift continues, manual synchronization burden

## Decision Outcome

**Chosen**: Option 1 (PyArrow Native Schema + Parquet-Only)

### Schema V2 Changes

**Breaking Changes**:

1. **Parquet date field**: STRING → `pa.date32()` (native DATE type)
2. **Parquet rank field**: `pa.int32()` → `pa.int64()` (consistency with DuckDB INTEGER)
3. **CSV format**: Deprecated (no longer generated)

**Rationale**:

- PyArrow is becoming "HTTP of data" (universal interchange format)
- DuckDB, Polars, Pandas all have zero-copy Arrow support
- Parquet files are self-describing (schema embedded in footer)
- CSV provides minimal value for analytical data (slow, large, untyped)

### Validation Enhancements

All builders now enforce:

- No duplicate (date, coin_id) pairs
- No NULL values in required fields (date, rank, coin_id)
- Rank range validation (1 to N, sequential)
- Market cap > 0 for all non-NULL values
- Schema conformance (exact column types)

### Migration Strategy

**No backward migration** - Fresh start approach:

- **Cutoff date**: 2025-11-24 (deployment date)
- **Historical data**: Remains v1 schema (STRING dates, INT32 ranks)
- **Future data**: Uses v2 schema (DATE dates, INT64 ranks)
- **User impact**: DuckDB auto-converts types in queries (transparent)

### Release Management

**GitHub Releases**:

- New tag pattern: `daily-YYYY-MM-DD` (perpetual storage)
- Keep `latest` tag pointing to most recent
- Monthly archives deprecated (per user choice)

## Consequences

### Positive

- ✅ **Type safety**: PyArrow enforces strict schemas, catches errors at build time
- ✅ **Single source of truth**: Schema defined once, used by all builders
- ✅ **Future-proof**: Apache Arrow ecosystem adopted by all modern data tools
- ✅ **Smaller artifacts**: Parquet 5x smaller than CSV (1-2 GB vs 8-12 GB uncompressed)
- ✅ **Faster queries**: DuckDB benchmark shows 2x faster Parquet reads vs CSV
- ✅ **Comprehensive validation**: Duplicate detection, null checking, range validation

### Negative

- ⚠️ **Breaking change**: Old Parquet files use different schema (STRING dates)
- ⚠️ **CSV deprecated**: Users expecting CSV need to adapt to Parquet
- ⚠️ **Validation overhead**: +10-15% build time (26 min → 29 min estimated)

### Neutral

- 📊 **Heterogeneous data**: v1 and v2 files coexist (DuckDB handles via CAST)
- 📊 **No backward compatibility**: Clean break, no migration scripts needed

## Validation

### Success Criteria

- [x] PyArrow type coercion prevents string→int errors
- [ ] Parquet files use `pa.date32()` and `pa.int64()` types
- [ ] DuckDB queries work seamlessly across v1/v2 schemas
- [ ] Full validation runs without errors (duplicates, nulls, ranges)
- [ ] Build completes in < 30 minutes
- [ ] GitHub Releases use `daily-YYYY-MM-DD` tags

### Rollback Plan

If critical issues discovered:

1. Revert to commit before schema change
2. Redeploy v1 schema
3. Create ADR amendment documenting failures
4. Reassess approach with additional research

## References

- [Apache Arrow Future-Proof Analysis](/research/future-proof-schema-2024.md) (internal research)
- [DuckDB CSV vs Parquet Benchmark 2024](https://duckdb.org/2024/12/05/csv-files-dethroning-parquet-or-not)
- [PyArrow Schema Documentation](https://arrow.apache.org/docs/python/api/datatypes.html)
- [Parquet Type System](https://parquet.apache.org/docs/file-format/types/)

## Related Decisions

- ADR-0002: CI/CD Daily Rankings Database (established builders pattern)
- ADR-0001: Hybrid Free Data Acquisition (established data sources)
