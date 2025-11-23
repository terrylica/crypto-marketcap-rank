# Pushover Notifications Setup

**Last Updated**: 2025-11-22 (Migrated to Doppler canonical source)

This document explains how to configure Pushover notifications for the daily collection workflow monitoring.

## Overview

The **Monitor Daily Collection** workflow automatically sends Pushover notifications when:

- ❌ Daily collection workflow **fails** (priority 1 - triggers sound)
- ✅ Daily collection workflow **succeeds** (priority -1 - silent)
- ⏳ Scheduled health check every 6 hours

## Canonical Architecture (as of 2025-11-22)

**Pushover credentials are stored in Doppler** (`notifications/dev`) - NOT as repository secrets.

- **Service Token**: `<your-doppler-token>`
- **Scope**: Read-only access to `notifications/dev` ONLY
- **Security**: Collaborators cannot access actual Pushover credentials

---

## Setup Steps

### Step 1: Add Doppler Service Token to GitHub

The repository only needs the Doppler service token (NOT the actual Pushover credentials):

```bash
# Using GitHub CLI (recommended)
gh secret set DOPPLER_TOKEN --repo terrylica/crypto-marketcap-rank
# Paste token when prompted: <your-doppler-token>
```

Or via GitHub web interface:

1. Go to https://github.com/terrylica/crypto-marketcap-rank/settings/secrets/actions
2. Click **New repository secret**
3. Name: `DOPPLER_TOKEN`
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
    DOPPLER_TOKEN: ${{ secrets.DOPPLER_TOKEN }}
  run: |
    # Fetch credentials from Doppler (canonical source)
    PUSHOVER_APP_TOKEN=$(doppler secrets get PUSHOVER_APP_TOKEN \
      --project notifications --config dev --plain)
    PUSHOVER_USER_KEY=$(doppler secrets get PUSHOVER_USER_KEY \
      --project notifications --config dev --plain)

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

- Update in Doppler (`notifications/dev`)
- All repositories automatically use new credentials
- No need to update 50+ repo secrets

✅ **Scoped access**

- Service token can ONLY read `notifications/dev`
- Cannot access publishing tokens (`claude-config/prd`)
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
   # Should show: DOPPLER_TOKEN
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
  --project notifications --config dev --plain)
export PUSHOVER_USER_KEY=$(doppler secrets get PUSHOVER_USER_KEY \
  --project notifications --config dev --plain)

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
notifications/
└── dev/
    ├── PUSHOVER_APP_TOKEN  (application token)
    └── PUSHOVER_USER_KEY   (user key)
```

### Service Token Details

**Token**: `<your-doppler-token>`

**Scope**:

- ✅ Can read: `notifications/dev`
- ❌ Cannot read: `claude-config/prd` (publishing tokens)
- ❌ Cannot read: Any other project

**Verification** (local):

```bash
# This works
DOPPLER_TOKEN="dp.st.dev..." doppler secrets --project notifications --config dev --only-names

# This fails (blocked by token scope)
DOPPLER_TOKEN="dp.st.dev..." doppler secrets --project claude-config --config prd --only-names
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

## Migration from Repository Secrets (Historical)

**Before (deprecated 2025-11-22)**:

- Pushover credentials stored as repository secrets
- Accessible to all collaborators with write access
- Required updating each repository individually

**After (current)**:

- Only Doppler service token in repository secrets
- Actual credentials in Doppler `notifications/dev`
- Single source of truth for all repositories

---

## References

- Pushover API: https://pushover.net/api
- Doppler CLI: https://docs.doppler.com/docs/cli
- GitHub Actions Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- Canonical Architecture: `/tmp/pushover_canonical_architecture_2025-11-22.md`

---

## Next Steps

After setup:

1. ✅ Add DOPPLER_TOKEN to GitHub repository secrets
2. ✅ Test with manual trigger
3. ✅ Wait for next scheduled run or daily collection
4. ✅ Verify notification received
5. ✅ Monitor for 1 week to ensure reliability
