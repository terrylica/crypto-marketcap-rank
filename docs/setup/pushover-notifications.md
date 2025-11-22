# Pushover Notifications Setup

This document explains how to configure Pushover notifications for the daily collection workflow monitoring.

## Overview

The **Monitor Daily Collection** workflow automatically sends Pushover notifications when:

- ❌ Daily collection workflow **fails** (priority 1 - triggers sound)
- ✅ Daily collection workflow **succeeds** (priority -1 - silent)
- ⏳ Scheduled health check every 6 hours

## Prerequisites

1. **Pushover Account**: Sign up at [pushover.net](https://pushover.net/)
2. **Pushover App**: Install on your phone (iOS/Android)

## Setup Steps

### Step 1: Get Pushover Credentials

1. **User Key**:

   - Log into https://pushover.net
   - Your **User Key** is displayed at the top right
   - Copy this 30-character string

2. **API Token**:
   - Go to https://pushover.net/apps/build
   - Create a new application:
     - Name: `Crypto MarketCap Rankings`
     - Description: `Daily collection workflow monitoring`
     - URL: `https://github.com/tainora/crypto-marketcap-rank`
     - Icon: (optional)
   - Click **Create Application**
   - Copy the **API Token/Key**

### Step 2: Add GitHub Secrets

Add the credentials as repository secrets:

```bash
# Using GitHub CLI (recommended)
gh secret set PUSHOVER_USER_KEY --repo tainora/crypto-marketcap-rank
# Paste your user key when prompted

gh secret set PUSHOVER_API_TOKEN --repo tainora/crypto-marketcap-rank
# Paste your API token when prompted
```

Or via GitHub web interface:

1. Go to https://github.com/tainora/crypto-marketcap-rank/settings/secrets/actions
2. Click **New repository secret**
3. Add:
   - Name: `PUSHOVER_USER_KEY`, Value: `<your-user-key>`
   - Name: `PUSHOVER_API_TOKEN`, Value: `<your-api-token>`

### Step 3: Verify Setup

Test the monitoring workflow:

```bash
# Trigger monitoring workflow manually
gh workflow run "Monitor Daily Collection" --repo tainora/crypto-marketcap-rank

# Wait a few seconds, then check status
gh run list --workflow "Monitor Daily Collection" --limit 1
```

You should receive a notification on your phone showing the status of the latest daily collection run.

## Notification Types

### Failure Notification (Priority 1)

Sent when daily collection fails:

```
🚨 Crypto MarketCap Rankings Collection Failed

Run ID: 19589282314
Branch: main
Time: 2025-11-22T03:01:58Z

Recent Errors:
- BuildError: Found 1693 duplicate (date, coin_id) pairs
- Process completed with exit code 1

View logs: https://github.com/...
```

**Behavior**: Triggers sound/vibration on your phone

### Success Notification (Priority -1)

Sent when daily collection succeeds:

```
✅ Crypto MarketCap Rankings Collection Succeeded

Run ID: 19589282315
Branch: main
Time: 2025-11-22T04:00:00Z

View artifacts: https://github.com/...
```

**Behavior**: Silent notification (no sound)

### Scheduled Health Check

Runs every 6 hours to verify monitoring is working.

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

## Troubleshooting

### No Notifications Received

1. **Check secrets are set**:

   ```bash
   gh secret list --repo tainora/crypto-marketcap-rank
   # Should show: PUSHOVER_API_TOKEN, PUSHOVER_USER_KEY
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
gh run view --log | grep -i pushover
```

Common issues:

- Invalid API token or user key
- Pushover API rate limit exceeded (30 messages/month free tier)
- Network connectivity issues

### Test Notification Manually

Use curl to test Pushover directly:

```bash
curl -s \
  --form-string "token=YOUR_API_TOKEN" \
  --form-string "user=YOUR_USER_KEY" \
  --form-string "message=Test notification from crypto-marketcap-rank" \
  https://api.pushover.net/1/messages.json
```

## Pushover Limits

**Free Tier**:

- 10,000 messages/month
- No message history
- Real-time notifications

**Pro Tier** ($5 one-time):

- Unlimited messages
- Custom notification sounds
- Desktop notifications

## Security Notes

- **Never commit** API tokens or user keys to git
- Secrets are encrypted in GitHub Actions
- Only repository admins can view/edit secrets
- Rotate tokens if compromised

## Monitoring Workflow File

Location: `.github/workflows/monitor-collection.yml`

Key features:

- Automatic failure detection
- Error log extraction
- Priority-based notifications
- Manual trigger support
- GitHub Actions summary

## Next Steps

After setup:

1. ✅ Add Pushover secrets to GitHub
2. ✅ Test with manual trigger
3. ✅ Wait for next scheduled run or daily collection
4. ✅ Verify notification received
5. ✅ Monitor for 1 week to ensure reliability

## References

- Pushover API: https://pushover.net/api
- GitHub Actions Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- desiderati/github-action-pushover: https://github.com/desiderati/github-action-pushover
