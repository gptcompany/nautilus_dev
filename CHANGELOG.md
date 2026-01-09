# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Ralph Loop autonomous execution mode for mechanical tasks
- Task Classifier v2 with dynamic learning and safeguards
- Agent spawn tracking (PreToolUse hook)
- Git auto-commit after Ralph iterations
- Pre-commit hooks (Bandit, Gitleaks, Ruff, Mypy)
- CodeQL static analysis in CI
- OSV vulnerability scanner in CI
- QuestDB metrics export (replaced InfluxDB)
- Grafana dashboards (PnL, Drawdown, Latency, Claude Metrics)
- ADR documentation (001-006)
- Incident management templates
- Docker staging environment

### Changed
- Migrated from InfluxDB to QuestDB for time-series metrics
- Updated CI/CD pipeline with security scanning stages
- Task classifier now uses confidence scoring and complexity analysis

### Deprecated
- InfluxDB configuration (see .env)
- alpha-debug agent (replaced by Ralph Loop)
- test-runner agent (replaced by Ralph Loop)
- tdd-guard agent (replaced by Ralph Loop)

### Removed
- P5 "Leggi Naturali" from Four Pillars (no empirical evidence)

### Fixed
- Mypy runtime NDArray cast errors
- Type annotation issues in strategies

### Security
- Added Bandit SAST scanning
- Added Gitleaks secrets detection
- Added Dependabot for dependency updates
- Added CodeQL for code scanning

## [0.1.0] - 2026-01-01

### Added
- Initial NautilusTrader development environment
- Four Pillars adaptive control framework
- Strategy templates and common utilities
- Documentation structure

---

[Unreleased]: https://github.com/user/nautilus_dev/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/user/nautilus_dev/releases/tag/v0.1.0
