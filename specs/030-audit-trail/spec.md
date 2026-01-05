# Feature Specification: Audit Trail System

**Feature Branch**: `030-audit-trail`
**Created**: 2026-01-05
**Status**: Draft
**Input**: Immutable logging for parameter changes, trades, and signals

## Overview

Our adaptive trading system has ~60 parameters that change dynamically. Without an immutable audit trail, we cannot:
- Debug trading failures post-mortem
- Detect parameter manipulation (Two Sigma fraud: $165M)
- Reconstruct what happened during crashes (Knight Capital: $440M in 45 min)

This feature creates an append-only logging system for all critical trading events.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Log Parameter Changes (Priority: P1)

As a quantitative developer, I want every parameter change logged immutably so that I can reconstruct system state at any point in time.

**Why this priority**: Parameter manipulation detection is the primary security requirement. Without this, fraud or bugs go undetected.

**Independent Test**: Can be verified by changing a parameter and querying the audit log to see the old/new values and timestamp.

**Acceptance Scenarios**:

1. **Given** a running trading system, **When** any parameter changes (risk multiplier, strategy weights, regime state), **Then** the change is logged with timestamp, old value, new value, and trigger reason.
2. **Given** a parameter change log entry, **When** I query by timestamp, **Then** I can see exactly what the system state was at that moment.
3. **Given** an attempt to modify historical logs, **When** the modification is attempted, **Then** the system rejects it (append-only enforcement).

---

### User Story 2 - Log Trade Executions (Priority: P1)

As a quantitative developer, I want every trade logged immutably so that I can verify execution quality and debug P&L discrepancies.

**Why this priority**: Trade execution is the core activity - without this, we cannot audit performance or detect slippage issues.

**Independent Test**: Can be verified by executing a trade and querying the audit log to see all execution details.

**Acceptance Scenarios**:

1. **Given** a trade execution, **When** the trade completes, **Then** the log captures: entry/exit flag, size, price, slippage, realized P&L, strategy source.
2. **Given** a trade log entry, **When** I query by order ID, **Then** I can reconstruct the full lifecycle (signal → order → fill → P&L).
3. **Given** multiple trades in a session, **When** I query the audit log, **Then** I can sum realized P&L and match the account balance change.

---

### User Story 3 - Log Signal Generation (Priority: P2)

As a quantitative developer, I want every signal logged so that I can analyze signal quality and strategy performance attribution.

**Why this priority**: Signals are upstream of trades - logging them allows root cause analysis of trading decisions.

**Independent Test**: Can be verified by generating a signal and querying the audit log to see signal value, regime, confidence.

**Acceptance Scenarios**:

1. **Given** a signal generation event, **When** a strategy produces a signal, **Then** the log captures: signal value, current regime, confidence score, source strategy.
2. **Given** a trade that was not executed, **When** I query the signal log, **Then** I can see why (signal below threshold, regime filter, risk limit hit).
3. **Given** a time range, **When** I query signals vs trades, **Then** I can compute signal-to-trade conversion rate per strategy.

---

### User Story 4 - Query Audit Trail (Priority: P2)

As a quantitative developer, I want to query the audit trail efficiently so that post-mortem analysis is fast.

**Why this priority**: An audit trail is useless if it cannot be queried quickly during incident response.

**Independent Test**: Can be verified by querying for events in a time range and measuring response time.

**Acceptance Scenarios**:

1. **Given** an audit trail with 1 million entries, **When** I query by time range (1 hour), **Then** results return in under 5 seconds.
2. **Given** an incident timestamp, **When** I query ±5 minutes around it, **Then** I see all parameter changes, signals, and trades in chronological order.
3. **Given** a strategy name, **When** I query all its events, **Then** I see a complete history of that strategy's behavior.

---

### Edge Cases

- What happens when disk space for logs runs out?
- How does the system handle logging during extreme market volatility (high event rate)?
- What if a log write fails mid-entry (system crash)?
- How are logs rotated without losing data?
- How is log integrity verified (corruption detection)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST log every parameter change with: timestamp, parameter name, old value, new value, trigger reason
- **FR-002**: System MUST log every trade execution with: timestamp, order ID, side (buy/sell), size, price, slippage, realized P&L, strategy source
- **FR-003**: System MUST log every signal with: timestamp, signal value, regime, confidence, source strategy
- **FR-004**: System MUST enforce append-only semantics (historical entries cannot be modified or deleted)
- **FR-005**: System MUST use structured format queryable for analysis
- **FR-006**: Logging latency MUST be under 1ms per event (minimal impact on trading performance)
- **FR-007**: System MUST support time-range queries returning results in under 5 seconds for 1 million entries
- **FR-008**: System MUST support filtering by event type (parameter, trade, signal)
- **FR-009**: System MUST support filtering by source (strategy name, component)
- **FR-010**: System MUST detect and report log corruption

### Key Entities

- **AuditEvent**: Base entity with timestamp, event type, source component
- **ParameterChangeEvent**: Parameter name, old value, new value, trigger reason
- **TradeEvent**: Order ID, side, size, price, slippage, P&L, strategy
- **SignalEvent**: Signal value, regime, confidence, strategy source
- **AuditQuery**: Time range, event type filter, source filter

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of parameter changes are logged (no silent changes)
- **SC-002**: 100% of trade executions are logged with full details
- **SC-003**: 100% of signals above threshold are logged
- **SC-004**: Log write latency is under 1ms per event (p99)
- **SC-005**: Query response time under 5 seconds for 1M entries
- **SC-006**: Log integrity is verifiable (corruption detectable)
- **SC-007**: Post-mortem reconstruction is possible for any point in time within retention period
- **SC-008**: Audit trail survives system crashes without data loss

## Assumptions

- Log retention period of 90 days is sufficient for most post-mortem analysis
- Structured format (one of: JSON Lines, Parquet) provides sufficient queryability
- Log rotation will be handled by external tooling (logrotate or similar)
- Checksums are sufficient for corruption detection (no cryptographic signing required)
- Storage is available for ~10GB per month of logs at normal trading activity

## Out of Scope

- Real-time alerting on log events (monitoring is separate feature)
- Log shipping to external systems (centralized logging is separate)
- Cryptographic signatures for regulatory compliance
- Cross-system correlation (only local audit trail)
- Log compression (handled by storage layer)

## Integration Points

- meta_controller.py - State transitions (VENTRAL/SYMPATHETIC/DORSAL)
- particle_portfolio.py - Strategy weight changes
- sops_sizing.py - Size calculations and risk multiplier changes
- alpha_evolve_bridge.py - Evolution triggers and performance updates
