# Pushover Notifications Setup

**Last Updated**: 2025-12-03 (Migrated to dedicated Doppler project)

**ADR**: [Pushover Doppler Integration](/docs/adr/2025-12-03-pushover-doppler-integration.md)

This document explains how to configure Pushover notifications for the daily collection workflow monitoring.

## Overview

The **Monitor Daily Collection** workflow automatically sends Pushover notifications when:

- ❌ Daily collection workflow **fails** (priority 1 - triggers sound)
- ✅ Daily collection workflow **succeeds** (priority -1 - silent)
- ⏳ Scheduled health check every 6 hours

## Canonical Architecture (as of 2025-12-03)

**Pushover credentials are stored in Doppler** (`crypto-marketcap-rank/prd`) - NOT as repository secrets.

- **Service Token**: `DOPPLER_TOKEN_CMR` (scoped to crypto-marketcap-rank/prd)
- **Scope**: Read-only access to `crypto-marketcap-rank/prd` ONLY
- **Security**: Collaborators cannot access actual Pushover credentials

---

## Setup Steps

### Step 1: Add Doppler Service Token to GitHub

The repository only needs the Doppler service token (NOT the actual Pushover credentials):

```bash
# Using GitHub CLI (recommended)
gh secret set DOPPLER_TOKEN_CMR --repo terrylica/crypto-marketcap-rank
# Paste token when prompted: <your-doppler-token>
```

Or via GitHub web interface:

1. Go to https://github.com/terrylica/crypto-marketcap-rank/settings/secrets/actions
2. Click **New repository secret**
3. Name: `DOPPLER_TOKEN_CMR`
4. Value: `<your-doppler-token>`

### Step 2: Verify Setup

The workflow will automatically fetch Pushover credentials from Doppler at runtime:

```bash
# Trigger monitoring workflow manually
gh workflow run "Monitor Daily Collection" --repo terrylica/crypto-marketcap-rank

# Wait a few seconds, then check status
gh run list --workflow "Monitor Daily Collection" --limit 1
```

You should receive a notification on your phone showing the status of the latest daily collection run.

---

## How It Works

### Workflow Credential Flow

```yaml
- name: Install Doppler CLI
  run: |
    curl -Ls https://cli.doppler.com/install.sh | sudo sh

- name: Send Pushover notification
  env:
    # ADR: 2025-12-03-pushover-doppler-integration - dedicated Doppler project
    DOPPLER_TOKEN: ${{ secrets.DOPPLER_TOKEN_CMR }}
  run: |
    # Fetch credentials from Doppler (canonical source)
    PUSHOVER_APP_TOKEN=$(doppler secrets get PUSHOVER_APP_TOKEN \
      --project crypto-marketcap-rank --config prd --plain)
    PUSHOVER_USER_KEY=$(doppler secrets get PUSHOVER_USER_KEY \
      --project crypto-marketcap-rank --config prd --plain)

    # Send notification
    curl -s \
      --form-string "token=$PUSHOVER_APP_TOKEN" \
      --form-string "user=$PUSHOVER_USER_KEY" \
      --form-string "message=Notification text" \
      https://api.pushover.net/1/messages.json
```

### Security Benefits

✅ **No credential exposure to collaborators**

- Only service token in repository secrets
- Actual credentials stay in Doppler

✅ **Easy credential rotation**

- Update in Doppler (`crypto-marketcap-rank/prd`)
- Workflows automatically use new credentials
- No need to update repository secrets

✅ **Scoped access**

- Service token can ONLY read `crypto-marketcap-rank/prd`
- Cannot access other Doppler projects
- Follows principle of least privilege

---

## Notification Types

### Failure Notification (Priority 1)

Sent when daily collection fails:

```
🚨 Crypto MarketCap Rankings Failed

Run: 19589282314
Repo: terrylica/crypto-marketcap-rank
Branch: main
Time: 2025-11-22T03:01:58Z

Errors:
- BuildError: Found 1693 duplicate (date, coin_id) pairs
- Process completed with exit code 1

https://github.com/terrylica/crypto-marketcap-rank/actions/runs/19589282314
```

**Behavior**: Triggers sound/vibration on your phone

### Success Notification (Priority -1)

Sent when daily collection succeeds:

```
✅ Crypto MarketCap Rankings Succeeded

Run: 19589282315
Repo: terrylica/crypto-marketcap-rank
Branch: main
Time: 2025-11-22T04:00:00Z

https://github.com/terrylica/crypto-marketcap-rank/actions/runs/19589282315
```

**Behavior**: Silent notification (no sound)

---

## Monitoring Workflow Triggers

1. **On Completion** (`workflow_run`):
   - Triggers immediately when daily collection completes
   - Sends notification based on success/failure

2. **Scheduled** (every 6 hours):
   - Backup monitoring in case webhook missed
   - Verifies monitoring workflow is healthy

3. **Manual** (`workflow_dispatch`):
   - For testing and verification
   - Can be triggered via GitHub UI or CLI

---

## Troubleshooting

### No Notifications Received

1. **Check Doppler token is set**:

   ```bash
   gh secret list --repo terrylica/crypto-marketcap-rank
   # Should show: DOPPLER_TOKEN_CMR
   ```

2. **Check Pushover app is installed** on your phone

3. **Verify workflow ran**:

   ```bash
   gh run list --workflow "Monitor Daily Collection" --limit 3
   ```

4. **Check workflow logs**:
   ```bash
   gh run view <run-id> --log
   ```

### Workflow Failed to Send Notification

Check the workflow logs for errors:

```bash
gh run view --log | grep -i -E "doppler|pushover"
```

Common issues:

- Doppler token invalid or revoked
- Doppler CLI installation failed
- Network connectivity issues
- Pushover API rate limit exceeded (10,000 messages/month free tier)

### Test Notification Manually (Local)

Use the canonical Doppler source:

```bash
# Load from Doppler (canonical source)
export PUSHOVER_APP_TOKEN=$(doppler secrets get PUSHOVER_APP_TOKEN \
  --project crypto-marketcap-rank --config prd --plain)
export PUSHOVER_USER_KEY=$(doppler secrets get PUSHOVER_USER_KEY \
  --project crypto-marketcap-rank --config prd --plain)

# Test notification
curl -s \
  --form-string "token=$PUSHOVER_APP_TOKEN" \
  --form-string "user=$PUSHOVER_USER_KEY" \
  --form-string "message=Test from crypto-marketcap-rank" \
  https://api.pushover.net/1/messages.json
```

---

## Doppler Architecture

### Credentials Location

```
crypto-marketcap-rank/
└── prd/
    ├── PUSHOVER_APP_TOKEN  (application token)
    └── PUSHOVER_USER_KEY   (user key)
```

### Service Token Details

**Token**: `DOPPLER_TOKEN_CMR` (stored in GitHub repository secrets)

**Scope**:

- ✅ Can read: `crypto-marketcap-rank/prd`
- ❌ Cannot read: Other Doppler projects
- ❌ Cannot read: Publishing tokens

**Verification** (local):

```bash
# This works (with DOPPLER_TOKEN_CMR)
DOPPLER_TOKEN="dp.st.prd..." doppler secrets --project crypto-marketcap-rank --config prd --only-names

# This fails (blocked by token scope)
DOPPLER_TOKEN="dp.st.prd..." doppler secrets --project claude-config --config prd --only-names
```

---

## Pushover Limits

**Free Tier**:

- 10,000 messages/month
- No message history
- Real-time notifications

**Pro Tier** ($5 one-time):

- Unlimited messages
- Custom notification sounds
- Desktop notifications

---

## Security Notes

- **Never commit** Doppler tokens or Pushover credentials to git
- Service token is read-only (cannot write/delete secrets)
- Token can be revoked in Doppler dashboard if compromised
- Actual Pushover credentials not accessible to repository collaborators

---

## Monitoring Workflow File

Location: `.github/workflows/monitor-collection.yml`

Key features:

- Doppler integration for secure credential access
- Automatic failure detection
- Error log extraction
- Priority-based notifications
- Manual trigger support
- GitHub Actions summary

---

## Migration History

**Before (deprecated 2025-11-22)**:

- Pushover credentials stored as repository secrets
- Accessible to all collaborators with write access
- Required updating each repository individually

**2025-11-22 (shared Doppler)**:

- Migrated to shared `notifications/dev` Doppler project
- Single service token for multiple repositories

**2025-12-03 (dedicated Doppler - current)**:

- ADR: [2025-12-03-pushover-doppler-integration](/docs/adr/2025-12-03-pushover-doppler-integration.md)
- Dedicated `crypto-marketcap-rank/prd` Doppler project
- Repository-specific notification identity (unique Pushover app)
- New service token: `DOPPLER_TOKEN_CMR`

---

## References

- Pushover API: https://pushover.net/api
- Doppler CLI: https://docs.doppler.com/docs/cli
- GitHub Actions Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- Canonical Architecture: `/tmp/pushover_canonical_architecture_2025-11-22.md`

---

## Next Steps

After setup:

1. ✅ Add DOPPLER_TOKEN_CMR to GitHub repository secrets
2. ✅ Test with manual trigger (`test-pushover.yml` workflow)
3. ✅ Wait for next scheduled run or daily collection
4. ✅ Verify notification received with new app identity
5. ✅ Monitor for 1 week to ensure reliability
