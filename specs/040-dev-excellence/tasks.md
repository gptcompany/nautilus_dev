# Tasks: Spec 040 - Development Excellence

## Phase 1: Security Base (Week 1)

### 1.1 Dependabot Configuration
- [ ] Enable Dependabot in GitHub repo settings
- [ ] Configure `dependabot.yml` for Python deps
- [ ] Set auto-merge for patch updates
- [ ] Configure weekly scan schedule

### 1.2 Bandit SAST Integration
- [ ] Add Bandit to CI pipeline
- [ ] Configure baseline for existing issues
- [ ] Set severity threshold (HIGH+)
- [ ] Add pre-commit hook for local check

### 1.3 Gitleaks Secrets Scanning
- [ ] Add Gitleaks to CI pipeline
- [ ] Create `.gitleaks.toml` config
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
- [ ] PnL Dashboard (real-time per strategy)
- [ ] Drawdown Dashboard (with threshold lines)
- [ ] Latency Dashboard (order execution)
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
- [ ] Create `.github/workflows/code-review.yml`
- [ ] Configure Claude Opus API call
- [ ] Define review criteria
- [ ] Add review comment posting
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
- [ ] Create `docker-compose.staging.yml`
- [ ] Configure testnet connections
- [ ] Separate QuestDB instance
- [ ] Separate Grafana instance

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
- [ ] Create `scripts/rollback.sh`
- [ ] Git tag management
- [ ] Docker image rollback
- [ ] Database state consideration
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
- [ ] Create `docs/adr/` directory
- [ ] Create ADR template
- [ ] Write ADR-001: Architecture Overview
- [ ] Write ADR-002: Data Storage Choice
- [ ] Write ADR-003: Risk Management Approach

### 6.2 Runbooks
- [ ] Create `docs/runbooks/` directory
- [ ] Deploy runbook
- [ ] Rollback runbook
- [ ] Incident response runbook
- [ ] On-call procedures

### 6.3 Incident Management
- [ ] Create `docs/incidents/` directory
- [ ] Create incident template
- [ ] Post-mortem template
- [ ] Incident log

### 6.4 Changelog
- [ ] Create/update CHANGELOG.md
- [ ] Define format (Keep a Changelog)
- [ ] Automate from commits

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
