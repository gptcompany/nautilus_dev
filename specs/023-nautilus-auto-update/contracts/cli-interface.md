# CLI Interface Contract

**Module**: `scripts.auto_update`
**Entry Point**: `python -m scripts.auto_update`

## Commands

### `check` - Analyze changelog for updates

```bash
$ python -m scripts.auto_update check [OPTIONS]

Arguments:
  None

Options:
  --changelog PATH    Path to changelog.json [default: docs/nautilus/nautilus-trader-changelog.json]
  --format TEXT       Output format: text, json, markdown [default: text]
  --verbose           Show detailed impact analysis

Exit Codes:
  0 - No updates needed or analysis complete
  1 - Error during analysis
  2 - Update available (for scripting)
```

**Output (text format)**:
```
=== NautilusTrader Update Check ===
Current Version: 1.221.0
Latest Version:  1.222.0
Status: UPDATE AVAILABLE

Breaking Changes (2):
  [HIGH] Removed deprecated `Strategy.on_tick` method
  [MEDIUM] Changed `BarType.from_str` signature

Impact Analysis:
  Files Affected: 5
  Lines Affected: 23
  Confidence Score: 72.5/100
  Recommendation: DELAYED (24h review window)
```

**Output (json format)**:
```json
{
  "update_available": true,
  "current_version": "1.221.0",
  "latest_version": "1.222.0",
  "impact_report": { ... }
}
```

---

### `update` - Perform auto-update

```bash
$ python -m scripts.auto_update update [OPTIONS]

Arguments:
  None

Options:
  --version TEXT      Specific version to update to [default: latest]
  --force             Update even with low confidence
  --dry-run           Show what would be done without making changes
  --skip-tests        Skip test validation (dangerous)
  --no-pr             Create branch but don't create PR

Exit Codes:
  0 - Update successful, PR created
  1 - Error during update
  2 - Update blocked (confidence too low, use --force)
  3 - Tests failed
```

**Output**:
```
=== NautilusTrader Auto-Update ===
Updating to version 1.222.0...

[1/4] Creating branch: update/v1.222.0
[2/4] Updating pyproject.toml
[3/4] Running uv sync
[4/4] Running tests...

Test Results:
  Passed: 142/145
  Failed: 3
  Duration: 45.2s

Tests failed. See test-results.json for details.
Update blocked. Use --force to override.
```

---

### `dispatch` - Dispatch Claude Code for complex fixes

```bash
$ python -m scripts.auto_update dispatch [OPTIONS]

Arguments:
  None

Options:
  --report PATH       Path to impact report JSON [default: auto-detect latest]
  --timeout INT       Timeout in seconds [default: 1800]
  --prompt TEXT       Custom task prompt [default: auto-generated]

Exit Codes:
  0 - Claude dispatch successful, PR created
  1 - Error during dispatch
  2 - Timeout reached
  3 - No impact report found
```

**Output**:
```
=== Claude Code Dispatch ===
Impact Report: /tmp/impact-report-1.222.0.json
Task Prompt: Fix NautilusTrader 1.222.0 breaking changes...

Dispatching Claude Code...
Agent ID: abc123

Waiting for completion (timeout: 30m)...
[============================] 100%

Claude Code completed.
PR Created: https://github.com/user/repo/pull/456
```

---

### `notify` - Send notification

```bash
$ python -m scripts.auto_update notify [OPTIONS] MESSAGE

Arguments:
  MESSAGE             Notification message

Options:
  --channel TEXT      Notification channel: discord, email, all [default: discord]
  --level TEXT        Level: info, warning, error, critical [default: info]
  --embed             Use rich embed (Discord only)
  --pr-url TEXT       Include PR link

Exit Codes:
  0 - Notification sent
  1 - Error sending notification
```

---

### `status` - Show pipeline status

```bash
$ python -m scripts.auto_update status

Output:
  Current Version: 1.221.0
  Last Check: 2025-12-29 05:00:00 UTC
  Pending PRs: 1 (update/v1.222.0)
  Pipeline Status: idle
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_WEBHOOK_URL` | No | Discord webhook for notifications |
| `GITHUB_TOKEN` | Yes | GitHub token for PR creation |
| `SMTP_USER` | No | SMTP username for email fallback |
| `SMTP_PASS` | No | SMTP password for email fallback |

---

## Configuration File

**Location**: `scripts/auto_update/config.toml` (optional)

```toml
[paths]
changelog = "docs/nautilus/nautilus-trader-changelog.json"
source_dirs = ["strategies", "scripts", "tests"]
pyproject = "pyproject.toml"

[git]
branch_prefix = "update/v"
remote = "origin"
base_branch = "master"

[confidence]
auto_merge_threshold = 85
delayed_merge_threshold = 65

[timeouts]
test_seconds = 600
claude_seconds = 1800

[notifications]
discord_webhook_url = "${DISCORD_WEBHOOK_URL}"
email_recipient = "sam@example.com"
```
