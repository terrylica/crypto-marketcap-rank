---
adr: 2025-12-03-pushover-doppler-integration
source: ~/.claude/plans/zazzy-enchanting-whale.md
implementation-status: in_progress
phase: phase-1
last-updated: 2025-12-03
---

# Implementation Spec: Pushover Doppler Integration

**ADR**: [Pushover Doppler Integration ADR](/docs/adr/2025-12-03-pushover-doppler-integration.md)

## Problem Statement

Create a dedicated Doppler project for crypto-marketcap-rank's Pushover notifications (separation of concerns), and update workflows to use the new credentials.

## Current State

| Aspect          | Current Value                                   |
| --------------- | ----------------------------------------------- |
| Doppler Project | `notifications`                                 |
| Doppler Config  | `dev`                                           |
| Secrets         | `PUSHOVER_APP_TOKEN`, `PUSHOVER_USER_KEY`       |
| GitHub Secret   | `DOPPLER_TOKEN` (scoped to `notifications/dev`) |

**Workflows Using Pushover:**

1. `.github/workflows/monitor-collection.yml` - Production monitoring (lines 92-154)
2. `.github/workflows/test-pushover.yml` - Test notifications (lines 20-144)

## Target State

| Aspect          | Target Value                                          |
| --------------- | ----------------------------------------------------- |
| Doppler Project | `crypto-marketcap-rank`                               |
| Doppler Config  | `prd`                                                 |
| Secrets         | `PUSHOVER_APP_TOKEN`, `PUSHOVER_USER_KEY` (new creds) |
| GitHub Secret   | `DOPPLER_TOKEN_CMR` (new, scoped to cmr/prd)          |

## New Credentials (Provided by User)

| Type                  | Value                            |
| --------------------- | -------------------------------- |
| Application/API Token | `aj4pnat5kib3qbs8zy6rrzhnevcws3` |
| User Key              | `ury88s1def6v16seeueoefqn1zbua1` |

## Implementation Tasks

### Task 1: Create Doppler Project and Config

```bash
# Create project
doppler projects create crypto-marketcap-rank

# Create prd config
doppler configs create prd --project crypto-marketcap-rank
```

**Success Criteria:**

- [x] Project `crypto-marketcap-rank` exists in Doppler
- [x] Config `prd` exists under the project

### Task 2: Add Secrets to Doppler

```bash
# Add the Pushover credentials
doppler secrets set PUSHOVER_APP_TOKEN="aj4pnat5kib3qbs8zy6rrzhnevcws3" \
  --project crypto-marketcap-rank --config prd

doppler secrets set PUSHOVER_USER_KEY="ury88s1def6v16seeueoefqn1zbua1" \
  --project crypto-marketcap-rank --config prd
```

**Success Criteria:**

- [x] `PUSHOVER_APP_TOKEN` stored in `crypto-marketcap-rank/prd`
- [x] `PUSHOVER_USER_KEY` stored in `crypto-marketcap-rank/prd`

### Task 3: Create Service Token

```bash
# Generate service token for GitHub Actions
doppler configs tokens create github-actions \
  --project crypto-marketcap-rank \
  --config prd
```

**Success Criteria:**

- [x] Service token generated (starts with `dp.st.`)
- [x] Token copied for GitHub secret

### Task 4: Add GitHub Repository Secret

Add new secret `DOPPLER_TOKEN_CMR` with the service token value.

```bash
# Via gh CLI
gh secret set DOPPLER_TOKEN_CMR --body "<service-token>"
```

**Success Criteria:**

- [x] `DOPPLER_TOKEN_CMR` secret exists in repository

### Task 5: Update monitor-collection.yml

Update Doppler project and GitHub secret references:

**Before:**

```yaml
env:
  DOPPLER_TOKEN: ${{ secrets.DOPPLER_TOKEN }}
```

```bash
PUSHOVER_APP_TOKEN=$(doppler secrets get PUSHOVER_APP_TOKEN --project notifications --config dev --plain)
PUSHOVER_USER_KEY=$(doppler secrets get PUSHOVER_USER_KEY --project notifications --config dev --plain)
```

**After:**

```yaml
env:
  DOPPLER_TOKEN: ${{ secrets.DOPPLER_TOKEN_CMR }}
```

```bash
PUSHOVER_APP_TOKEN=$(doppler secrets get PUSHOVER_APP_TOKEN --project crypto-marketcap-rank --config prd --plain)
PUSHOVER_USER_KEY=$(doppler secrets get PUSHOVER_USER_KEY --project crypto-marketcap-rank --config prd --plain)
```

**Success Criteria:**

- [x] `DOPPLER_TOKEN_CMR` used instead of `DOPPLER_TOKEN`
- [x] Project updated to `crypto-marketcap-rank`
- [x] Config updated to `prd`

### Task 6: Update test-pushover.yml

Same changes as Task 5 for the test workflow.

**Success Criteria:**

- [x] `DOPPLER_TOKEN_CMR` used instead of `DOPPLER_TOKEN`
- [x] Project updated to `crypto-marketcap-rank`
- [x] Config updated to `prd`

### Task 7: Update Documentation

Update `docs/setup/pushover-notifications.md` with new Doppler project details.

**Success Criteria:**

- [x] Documentation reflects new project/config names

## Validation

After implementation:

1. Run `test-pushover.yml` workflow manually
2. Verify notifications arrive with new app identity/logo
3. Monitor next daily collection for production verification

## Files to Modify

| File                                       | Changes                                       |
| ------------------------------------------ | --------------------------------------------- |
| `.github/workflows/monitor-collection.yml` | Update Doppler project, config, GitHub secret |
| `.github/workflows/test-pushover.yml`      | Update Doppler project, config, GitHub secret |
| `docs/setup/pushover-notifications.md`     | Update documentation                          |
