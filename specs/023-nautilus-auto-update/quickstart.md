# Quickstart: NautilusTrader Auto-Update Pipeline

## Prerequisites

- Python 3.11+
- `uv` package manager
- `gh` CLI (authenticated)
- Claude Code CLI (for dispatch)
- Discord webhook URL (optional)

## Installation

```bash
# The auto_update module is part of scripts/
# No separate installation needed

# Verify dependencies
uv run python -m scripts.auto_update --help
```

## Basic Usage

### 1. Check for Updates

```bash
# Simple check
uv run python -m scripts.auto_update check

# JSON output for scripting
uv run python -m scripts.auto_update check --format json

# Verbose with file-level impact
uv run python -m scripts.auto_update check --verbose
```

### 2. Preview Impact

```bash
# Dry-run to see what would happen
uv run python -m scripts.auto_update update --dry-run
```

### 3. Auto-Update (if safe)

```bash
# Standard update (respects confidence thresholds)
uv run python -m scripts.auto_update update

# Force update (ignores low confidence)
uv run python -m scripts.auto_update update --force

# Update without creating PR (local branch only)
uv run python -m scripts.auto_update update --no-pr
```

### 4. Dispatch Claude Code

```bash
# For complex breaking changes
uv run python -m scripts.auto_update dispatch

# With custom prompt
uv run python -m scripts.auto_update dispatch \
  --prompt "Focus on strategies/production/ directory only"
```

## Configuration

### Environment Variables

```bash
# Required for PR creation
export GITHUB_TOKEN="ghp_..."

# Optional: Discord notifications
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Optional: Email fallback
export SMTP_USER="user@gmail.com"
export SMTP_PASS="app-password"
```

### Config File (optional)

Create `scripts/auto_update/config.toml`:

```toml
[confidence]
auto_merge_threshold = 85
delayed_merge_threshold = 65

[notifications]
discord_webhook_url = "${DISCORD_WEBHOOK_URL}"
```

## Automated Scheduling

### GitHub Actions (version check)

Already configured in `.github/workflows/nautilus-update-check.yml`:
- Runs daily at 04:00 UTC
- Triggers Discord notification if update available

### Local Cron (heavy operations)

Add to crontab:

```bash
# Daily at 05:00 local time (after GH Actions)
0 5 * * * cd /media/sam/1TB/nautilus_dev && uv run python -m scripts.auto_update update 2>&1 | tee /var/log/nautilus-update.log
```

## Common Workflows

### Manual Update Flow

```bash
# 1. Check what's new
uv run python -m scripts.auto_update check --verbose

# 2. Review output, then update
uv run python -m scripts.auto_update update

# 3. If tests fail, dispatch Claude
uv run python -m scripts.auto_update dispatch
```

### Monitoring Updates

```bash
# Check pipeline status
uv run python -m scripts.auto_update status

# List pending update PRs
gh pr list --label "auto-update"
```

## Troubleshooting

### "Confidence too low"

The update has breaking changes. Options:
1. Use `--force` to override
2. Use `dispatch` to let Claude Code fix it
3. Fix manually and mark PR as ready

### "Tests failed"

```bash
# View test failures
cat test-results.json | jq '.failed_test_names'

# Re-run specific tests
uv run pytest tests/test_failing.py -v
```

### "PR creation failed"

```bash
# Check GitHub auth
gh auth status

# Manually create PR
gh pr create --base master --head update/v1.222.0
```

## Integration with Existing Workflow

This pipeline integrates with:
- **N8N**: Consumes `docs/nautilus/nautilus-trader-changelog.json`
- **test-runner agent**: Validates updates
- **github-workflow skill**: PR creation
- **alpha-debug**: Post-update verification
