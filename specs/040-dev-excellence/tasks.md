# Tasks: Spec 040 - Development Excellence

## Phase 1: Security Base (Week 1)

### 1.1 Dependabot Configuration
- [ ] Enable Dependabot in GitHub repo settings
- [ ] Configure `dependabot.yml` for Python deps
- [ ] Set auto-merge for patch updates
- [ ] Configure weekly scan schedule

### 1.2 Bandit SAST Integration
- [x] Add Bandit to CI pipeline
- [x] Configure baseline for existing issues
- [x] Set severity threshold (HIGH+)
- [ ] Add pre-commit hook for local check

### 1.3 Gitleaks Secrets Scanning
- [x] Add Gitleaks to CI pipeline
- [x] Create `.gitleaks.toml` config
- [ ] Scan history for existing secrets
- [ ] Add pre-commit hook

### 1.4 Sentry Error Tracking
- [ ] Create Sentry project (free tier)
- [ ] Install sentry-sdk in project
- [ ] Configure DSN in environment
- [ ] Add Sentry to trading strategies
- [ ] Configure alert rules
- [ ] Test error capture

## Phase 2: Monitoring Stack (Week 2)

### 2.1 QuestDB Setup
- [ ] Verify QuestDB running (from Spec 005)
- [ ] Create trading metrics tables
- [ ] Configure retention policies
- [ ] Test data ingestion

### 2.2 Grafana Dashboards
- [x] PnL Dashboard (real-time per strategy)
- [x] Drawdown Dashboard (with threshold lines)
- [x] Latency Dashboard (order execution)
- [ ] Error Rate Dashboard
- [ ] Positions Dashboard (open positions)

### 2.3 Alert Rules
- [ ] Drawdown > 5% Warning
- [ ] Drawdown > 10% Critical
- [ ] Error rate > 1% Warning
- [ ] Position > MAX Critical
- [ ] Connection lost Immediate

### 2.4 Telegram Bot Integration
- [ ] Create Telegram bot
- [ ] Configure Grafana notification channel
- [ ] Link alerts to Telegram
- [ ] Test alert delivery
- [ ] Document bot setup

### 2.5 Metrics Collection
- [ ] Add MetricsCollector to TradingNode
- [ ] Emit PnL updates
- [ ] Emit order latency
- [ ] Emit position changes
- [ ] Emit error events

## Phase 3: Code Review System (Week 3)

### 3.1 Opus Reviewer Workflow
- [x] Create `.github/workflows/code-review.yml`
- [x] Configure Claude Opus API call
- [x] Define review criteria
- [x] Add review comment posting
- [ ] Test on sample PR

### 3.2 Review Checklist
- [ ] Create `docs/review-checklist.md`
- [ ] Trading-specific checks
- [ ] Security checks
- [ ] Performance checks
- [ ] NT best practices

### 3.3 Security Review Focus
- [ ] Input validation checks
- [ ] API key handling
- [ ] Position limit enforcement
- [ ] Error handling review

## Phase 4: Staging Environment (Week 3)

### 4.1 Docker Staging Setup
- [x] Create `docker-compose.staging.yml`
- [x] Configure testnet connections
- [x] Separate QuestDB instance
- [x] Separate Grafana instance

### 4.2 Testnet Configuration
- [ ] Binance Testnet credentials
- [ ] Bybit Testnet credentials
- [ ] Paper trading mode
- [ ] Test order execution

### 4.3 Staging Deploy Script
- [ ] Create `scripts/deploy-staging.sh`
- [ ] Build Docker images
- [ ] Run migrations
- [ ] Health checks
- [ ] Smoke tests

## Phase 5: Rollback & Recovery (Week 3)

### 5.1 Rollback Script
- [x] Create `scripts/rollback.sh`
- [x] Git tag management
- [x] Docker image rollback
- [x] Database state consideration
- [ ] Test rollback procedure

### 5.2 State Snapshot
- [ ] Pre-deploy state capture
- [ ] Position snapshot
- [ ] Config backup
- [ ] Recovery validation

### 5.3 Recovery Runbook
- [ ] Create `docs/runbooks/recovery.md`
- [ ] Step-by-step procedure
- [ ] Contact information
- [ ] Escalation path

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
- [ ] On-call procedures

### 6.3 Incident Management
- [x] Create `docs/incidents/` directory
- [x] Create incident template
- [x] Post-mortem template
- [x] Incident log (README.md)

### 6.4 Changelog
- [ ] Create/update CHANGELOG.md
- [ ] Define format (Keep a Changelog)
- [ ] Automate from commits

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

### 7.6 CodSpeed Benchmarking (Future)
- [ ] Evaluate CodSpeed for Python benchmarks
- [ ] Create baseline benchmarks
- [ ] Integrate with CI

### 7.7 Rust Tooling (Future - When Needed)
- [ ] cargo-vet for supply chain
- [ ] cargo-deny for deps/licenses

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
- [ ] Add rate limiting (100 calls/hour) - future

### 8.3 Progress Persistence
- [x] Create `.ralph/progress.md` format
- [x] Auto-update on each iteration
- [ ] Git commit progress after each loop
- [ ] Resume from last progress on restart

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
- [ ] Ralph iteration count in Grafana
- [ ] Token usage tracking
- [ ] Circuit breaker triggers
- [ ] Success/failure rates

### 8.6 Integration
- [x] Settings.json updated with new hooks
- [ ] RALPH_MODE env var activation (optional)
- [ ] PROMPT.md template
- [ ] Documentation and examples

### 8.7 Agent Deprecation
- [x] Create deprecation plan (ADR-006)
- [ ] Add deprecation warnings to old agents
- [ ] Update CLAUDE.md with new execution modes
- [ ] Remove deprecated agents after 30 days

## Verification

### Security Verification
- [ ] Run `bandit -r strategies/` - zero HIGH
- [ ] Run `gitleaks detect` - zero secrets
- [ ] Check Dependabot alerts - zero CRITICAL
- [ ] Trigger test error - appears in Sentry

### Monitoring Verification
- [ ] Execute test trade - appears in dashboard
- [ ] Trigger drawdown - alert received
- [ ] Check latency - metrics visible
- [ ] Verify Telegram - message received

### Review Verification
- [ ] Create test PR - Opus review appears
- [ ] Check review quality - actionable feedback
- [ ] Security items - flagged correctly

### Staging Verification
- [ ] Deploy to staging - success
- [ ] Run backtest - completes
- [ ] Paper trade - orders execute
- [ ] Metrics flow - visible in staging Grafana

### Rollback Verification
- [ ] Execute rollback - completes < 5 min
- [ ] Verify state - consistent
- [ ] Trading resumes - functional
