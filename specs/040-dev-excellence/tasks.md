# Tasks: Spec 040 - Development Excellence

## Phase 1: Security Base (Week 1)

### 1.1 Dependabot Configuration
- [x] Enable Dependabot in GitHub repo settings (già attivo)
- [x] Configure `dependabot.yml` for Python deps
- [x] Set auto-merge for patch updates
- [x] Configure weekly scan schedule

### 1.2 Bandit SAST Integration
- [x] Add Bandit to CI pipeline
- [x] Configure baseline for existing issues
- [x] Set severity threshold (HIGH+)
- [x] Add pre-commit hook for local check

### 1.3 Gitleaks Secrets Scanning
- [x] Add Gitleaks to CI pipeline
- [x] Create `.gitleaks.toml` config
- [x] Scan history for existing secrets (2026-01-08: 3 false positives allowlisted)
- [x] Add pre-commit hook

### 1.4 Sentry Error Tracking
- [x] Create Sentry project (free tier)
- [x] Install sentry-sdk in project
- [x] Configure DSN in environment
- [x] Add Sentry to trading strategies (sentry_integration.py)
- [x] Create `scripts/setup_sentry_alerts.py` (API automation)
- [x] Run setup_sentry_alerts.py (completed 2026-01-08: 4 alert rules created)
- [x] Test error capture (verified 2026-01-08)

### 1.5 Sentry MCP Integration
- [x] Add Sentry MCP server to Claude Code
- [x] Update agents with Sentry tools (nautilus-coder, nautilus-live-operator, backtest-analyzer)
- [ ] Authenticate via OAuth (restart Claude session)

## Phase 2: Monitoring Stack (Week 2)

### 2.1 QuestDB Setup
- [x] Verify QuestDB running (from Spec 005) - verified 2026-01-08
- [x] Create trading metrics tables (trading_pnl, order_latency, position_changes, trading_errors)
- [x] Configure retention policies (maxUncommittedRows)
- [x] Test data ingestion (ILP protocol on port 9009)

### 2.2 Grafana Dashboards
- [x] PnL Dashboard (real-time per strategy)
- [x] Drawdown Dashboard (with threshold lines)
- [x] Latency Dashboard (order execution)
- [x] Error Rate Dashboard
- [x] Positions Dashboard (open positions)

### 2.3 Alert Rules
- [x] Drawdown > 5% Warning (rules.yml)
- [x] Drawdown > 10% Critical (rules.yml)
- [x] Error rate > 1% Warning (rules.yml)
- [x] Position > MAX Critical (rules.yml)
- [x] Connection lost Immediate (rules.yml)

### 2.4 Discord Alert Integration (Changed from Telegram)
- [x] Create Discord webhook (via setup script)
- [x] Discord webhook tested (verified 2026-01-08: message delivered)
- [x] Configure Grafana notification channel (API: contact-points/discord-trading)
- [x] Link alerts to Discord (default receiver updated)
- [x] Test alert delivery (verified 2026-01-08: status=ok)
- [x] Document bot setup

### 2.5 Metrics Collection
- [x] Add MetricsCollector to TradingNode (metrics_collector.py)
- [x] Emit PnL updates (emit_pnl)
- [x] Emit order latency (emit_order_latency)
- [x] Emit position changes (emit_position_change)
- [x] Emit error events (emit_error)

## Phase 3: Code Review System (Week 3)

### 3.1 Opus Reviewer Workflow
- [x] Create `.github/workflows/code-review.yml`
- [x] Configure Claude Opus API call
- [x] Define review criteria
- [x] Add review comment posting
- [ ] Test on sample PR

### 3.2 Review Checklist
- [x] Create `docs/review-checklist.md`
- [x] Trading-specific checks
- [x] Security checks
- [x] Performance checks
- [x] NT best practices

### 3.3 Security Review Focus
- [x] Input validation checks (Rating: A- Pydantic v2 on all critical configs)
- [x] API key handling (Rating: A+ env vars only, Sentry PII filtering)
- [x] Position limit enforcement (Rating: A multi-layer: config+runtime+PID)
- [x] Error handling review (Rating: A no silent failures, proper logging)

## Phase 4: Staging Environment (Week 3)

### 4.1 Docker Staging Setup
- [x] Create `docker-compose.staging.yml`
- [x] Configure testnet connections
- [x] Separate QuestDB instance
- [x] Separate Grafana instance

### 4.2 Testnet Configuration
- [x] ~~Binance Testnet credentials~~ (deprecated: unstable)
- [x] ~~Bybit Testnet credentials~~ (deprecated: unstable)
- [x] Hyperliquid Testnet configured (docker-compose.staging.yml)
- [x] HYPERLIQUID_TESTNET_PK in .env
- [x] Paper trading mode (Hyperliquid testnet connection verified)
- [x] Test order execution (verified 2026-01-08: place + cancel OK)

### 4.3 Staging Deploy Script
- [x] Create `scripts/deploy-staging.sh`
- [x] Build Docker images
- [x] Run migrations
- [x] Health checks
- [x] Smoke tests

## Phase 5: Rollback & Recovery (Week 3)

### 5.1 Rollback Script
- [x] Create `scripts/rollback.sh`
- [x] Git tag management
- [x] Docker image rollback
- [x] Database state consideration
- [ ] Test rollback procedure

### 5.2 State Snapshot
- [x] Pre-deploy state capture (scripts/state_snapshot.py)
- [x] Position snapshot (included in state_snapshot.py)
- [x] Config backup (included in state_snapshot.py)
- [ ] Recovery validation

### 5.3 Recovery Runbook
- [x] Create `docs/runbooks/recovery.md`
- [x] Step-by-step procedure
- [x] Contact information
- [x] Escalation path

## Phase 6: Knowledge Management (Ongoing)

### 6.1 ADR System
- [x] Create `docs/adr/` directory
- [x] Create ADR template
- [x] Write ADR-001: Architecture Overview
- [x] Write ADR-002: Data Storage Choice
- [x] Write ADR-003: Risk Management Approach

### 6.2 Runbooks
- [x] Create `docs/runbooks/` directory
- [x] Deploy runbook
- [x] Rollback runbook
- [x] Incident response runbook
- [x] On-call procedures (docs/runbooks/on-call.md)

### 6.3 Incident Management
- [x] Create `docs/incidents/` directory
- [x] Create incident template
- [x] Post-mortem template
- [x] Incident log (README.md)

### 6.4 Changelog
- [x] Create/update CHANGELOG.md
- [x] Define format (Keep a Changelog)
- [x] Automate from commits (N8N: NautilusTrader-Version-Monitor-v2 @ /media/sam/1TB/N8N_dev)

## Phase 7: NT-Inspired Improvements

### 7.1 CodeQL Static Analysis
- [x] Create `.github/workflows/codeql.yml`
- [x] Configure for Python
- [x] Weekly + PR trigger
- [x] SARIF upload to GitHub Security

### 7.2 Pytest Optimization
- [x] Enable pytest-xdist parallel
- [x] Configure automatic retries (flaky tests)
- [x] Update CI to use `-n auto` (via pyproject.toml)

### 7.3 OSV Scanner
- [x] Add osv-scanner to security stage
- [x] Configure lockfile scanning
- [x] Non-blocking (advisory only)

### 7.4 Discord Alerting
- [x] Create Discord webhook setup script
- [x] Configure Grafana contact point
- [x] Link critical alerts to Discord
- [ ] Test drawdown alert (requires webhook setup)

### 7.5 Claude Metrics Dashboard
- [x] Create Grafana dashboard for claude_* tables
- [x] Session duration, tool calls, errors
- [x] TDD compliance visualization

## Phase 10: Language-Specific Tooling

> Tasks separated by language. Activate when codebase includes that language.

### 10.1 Python Tooling (Active)
- [x] Bandit SAST (security)
- [x] Ruff linting
- [x] Pytest + coverage
- [x] CodSpeed benchmarking (2026-01-08: .github/workflows/benchmarks.yml)
  - [x] Evaluate CodSpeed for Python benchmarks
  - [x] Create benchmark directory + README (tests/benchmarks/)
  - [x] Integrate with CI (pytest-codspeed)

### 10.2 Rust Tooling (Conditional - triggers when .rs files change)
> Auto-activates via detect-changes job in ci-cd-pipeline.yml

- [x] cargo-audit for vulnerability scanning (2026-01-08: Stage 6 in CI)
- [x] cargo-deny for deps/licenses (2026-01-08: Stage 6 in CI)
- [x] Clippy linting in CI (2026-01-08: Stage 6 in CI)
- [x] ~~cargo-vet~~ (removed: overkill for solo dev, requires manual audit of each crate)
- [ ] Miri for undefined behavior detection (optional, future)

## Phase 8: Autonomous AI Loops (Ralph + AlphaEvolve Hybrid)

### 8.1 Analysis & Decision
- [x] Research Ralph Wiggum pattern
- [x] Compare with AlphaEvolve approach
- [x] Document in ADR-004
- [ ] Team review of ADR-004

### 8.2 Ralph-Lite Mode Implementation
- [x] Create `hooks/control/ralph-loop.py`
- [x] Implement exit interception (exit code 2)
- [x] Add iteration tracking `.ralph/state.json`
- [x] Implement circuit breakers:
  - MAX_CONSECUTIVE_ERRORS=3
  - MAX_NO_PROGRESS=5
  - MAX_ITERATIONS=15
- [x] Add rate limiting (100 calls/hour, 10s min interval)

### 8.3 Progress Persistence
- [x] Create `.ralph/progress.md` format
- [x] Auto-update on each iteration
- [x] Git commit progress after each loop
- [x] Resume from last progress on restart (2026-01-09: ralph-resume.py hook implemented)

### 8.4 Task Classifier
- [x] Create task classification logic
- [x] Mechanical → Ralph mode
- [x] Creative → AlphaEvolve mode
- [x] Standard → Current workflow
- [x] Add to prompt submission hook
- [x] Add safeguards (user confirmation for low confidence)
- [x] Add complexity scoring (penalizes Ralph for creative tasks)
- [x] Add dynamic learning (keyword weights adjust from outcomes)
- [x] Add escape hatch ("STOP RALPH", "RALPH STATUS" commands)
- [x] Add token budget awareness

### 8.5 Monitoring Dashboard
- [x] Ralph iteration count in Grafana (monitoring/grafana/dashboards/claude_metrics.json)
- [x] Agent spawn tracking (PreToolUse hook → agent_spawns.jsonl)
- [ ] Token usage per agent (blocked: Issue #10388)
- [x] Circuit breaker triggers (in claude_metrics.json)
- [x] Success/failure rates (in claude_metrics.json)

### 8.6 Integration
- [x] Settings.json updated with new hooks
- [x] RALPH_MODE env var activation (.env.example updated)
- [x] PROMPT.md template (.claude/PROMPT.md)
- [x] Documentation and examples (included in PROMPT.md)

### 8.7 Agent Deprecation
- [x] Create deprecation plan (ADR-006)
- [x] Add deprecation warnings to old agents
- [x] Update CLAUDE.md with new execution modes
- [ ] Remove deprecated agents after 30 days (scheduled)

### 8.8 Ralph Enterprise Hardening (2026-01-09)
> Upgrade Ralph from MVP to enterprise-grade based on audit findings.

#### 8.8.1 Resume from Restart
- [x] Create `ralph-resume.py` UserPromptSubmit hook (2026-01-09)
- [x] Detect active state.json on session start (2026-01-09)
- [x] Offer resume/discard options to user (2026-01-09: RALPH RESUME/DISCARD commands)
- [x] Restore iteration count and progress context (2026-01-09)
- [ ] Test resume after crash/restart

#### 8.8.2 SSOT Configuration
- [x] Add ralph section to `config/canonical.yaml` (2026-01-09)
- [x] Load MAX_ITERATIONS from SSOT (2026-01-09)
- [x] Load MAX_BUDGET_USD from SSOT (2026-01-09)
- [x] Load circuit breaker thresholds from SSOT (2026-01-09)
- [x] Fallback to defaults if missing (2026-01-09)

#### 8.8.3 Structured Logging
- [x] Replace print() with logging module (2026-01-09)
- [x] Add JSON structured log format (2026-01-09: ~/.claude/logs/)
- [x] Integrate Sentry for error tracking (2026-01-09: emit_sentry_breadcrumb())
- [x] Add QuestDB metrics emission (2026-01-09: emit_questdb_metric() via ILP)
- [ ] Update Grafana dashboard with live Ralph metrics

#### 8.8.4 Error Handling
- [x] Remove all `except: pass` patterns (2026-01-09)
- [x] Add proper error logging with context (2026-01-09)
- [x] Add Sentry breadcrumbs for debugging (2026-01-09)
- [x] Implement graceful degradation (2026-01-09: non-critical failures logged but don't stop loop)

#### 8.8.5 State Management
- [ ] Add file locking for state.json
- [x] Add state validation/checksum (2026-01-09)
- [x] Add automatic backup before mutations (2026-01-09: state.json.bak)
- [ ] Add state recovery from backup

#### 8.8.6 Testing
- [x] Create tests/hooks/test_ralph_loop.py (2026-01-09: claude-hooks-shared/tests/hooks/)
- [x] Test circuit breakers trigger correctly (2026-01-09: mock tests)
- [x] Test resume from state.json (2026-01-09: mock tests)
- [x] Test rate limiting (2026-01-09: mock tests)
- [x] Mock test for verification scenarios (2026-01-09: TestVerificationScenarios class)

## Verification

### Quick Verification (New Sessions)
```bash
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
python scripts/verify_spec040.py
```

### Security Verification
- [x] Run `bandit -r strategies/` - zero HIGH (verified 2026-01-08: 0 HIGH, 3 Medium/Low confidence)
- [x] Run `gitleaks detect` - zero secrets (verified 2026-01-08: 0 after allowlist config)
- [ ] Check Dependabot alerts - zero CRITICAL
- [x] Trigger test error - appears in Sentry (verified 2026-01-08)

### Monitoring Verification
- [x] Execute test trade - appears in dashboard (verified 2026-01-08: MetricsCollector emits to QuestDB)
- [ ] Trigger drawdown - alert received (Discord configured, needs alert rule test)
- [x] Check latency - metrics visible (verified 2026-01-08: trading_orders.latency_ms populated)
- [x] Verify Discord - message received (verified 2026-01-08: test alert delivered)

### Review Verification
- [ ] Create test PR - Opus review appears
- [ ] Check review quality - actionable feedback
- [ ] Security items - flagged correctly

### Staging Verification
- [ ] Deploy to staging - success
- [ ] Run backtest - completes
- [x] Paper trade - orders execute (verified 2026-01-08: Hyperliquid testnet BTC limit buy+cancel OK)
- [x] Metrics flow - visible in staging Grafana (verified 2026-01-08: 4 pnl, 3 orders, 3 risk records)

### Rollback Verification
- [ ] Execute rollback - completes < 5 min
- [ ] Verify state - consistent
- [ ] Trading resumes - functional

## Phase 9: Architecture Documentation Sync

### 9.1 Architecture Drift Detection
- [x] Create `scripts/architecture_drift_detector.py`
- [x] Track ports (QuestDB, Grafana, Redis)
- [x] Track versions (NautilusTrader, Python)
- [x] Track paths (catalog, nightly env)
- [x] JSON output for CI (--json flag)
- [x] Auto-fix capability (--fix flag)

### 9.2 Pre-commit Integration
- [x] Add architecture-drift hook to `.pre-commit-config.yaml`
- [x] Trigger on .env, docker-compose*.yml, ARCHITECTURE.md changes
- [x] Test hook on commit (verified 2026-01-08: hook detects drift correctly)

### 9.3 CI Integration
- [x] Add drift check to CI pipeline (warning only, non-blocking)
- [x] Block PR on drift (2026-01-08: exits with error on config drift)
- [x] Auto-create PR to update docs (2026-01-08: .github/workflows/auto-fix-drift.yml)

### 9.4 Expanded Tracking
- [x] Track database schemas (2026-01-08: TRACKED_TABLES + check_questdb_tables())
- [x] Track API versions (2026-01-08: GRAFANA_VERSION, QUESTDB_VERSION in TRACKED_CONFIGS)
- [x] Track dependency versions (Dependabot: pip, docker, github-actions)
- [x] Triple comparison pyproject↔installed↔docs (2026-01-08: check_pyproject_sync())

### 9.5 SSOT (Single Source of Truth)
- [x] Create `config/canonical.yaml` as authoritative config source (2026-01-08)
- [x] Update drift detector to load from canonical.yaml dynamically (2026-01-08)
- [x] Add SSOT section to CLAUDE.md (2026-01-08)
- [x] Fallback to hardcoded values if canonical.yaml missing (2026-01-08)
