# Feature Specification: Deribit Options Data Pipeline

**Feature Branch**: `042-deribit-options-data`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Deribit Options Data Pipeline - Historical and real-time options data from Deribit via CCXT including IV surface, Greeks, term structure, and volatility smile. Supports options analytics for position sizing, regime detection enhancement, and vol arbitrage signals. Aligned with P1-P4 pillars using regime-switching Heston calibration."

## Problem Statement

Options data provides critical market intelligence unavailable from perpetual futures alone:

- **Implied Volatility**: Forward-looking vol expectations from market prices
- **Skew/Smile**: Put-call asymmetry indicating directional bias
- **Term Structure**: Short vs long-term vol expectations (contango/backwardation)
- **Greeks**: Delta, gamma, vega exposure for hedging and sizing

Currently, traders using NautilusTrader have no integrated way to:
- Fetch historical/real-time options data from Deribit
- Calibrate volatility models for options pricing
- Use IV signals in perpetual trading strategies

## Four Pillars Alignment

| Pillar | Alignment | Implementation |
|--------|-----------|----------------|
| P1 (Probabilistico) | IV surface provides probability distributions | Options imply risk-neutral densities |
| P2 (Non Lineare) | Skew captures fat-tail expectations | Put skew = tail risk premium |
| P3 (Non Parametrico) | Regime-switching parameters | Heston params updated by regime state |
| P4 (Scalare) | Multi-tenor term structure | 1D, 7D, 30D, 90D+ IV tracked |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fetch Options Chain Snapshot (Priority: P1) MVP

As a trader, I want to fetch the current options chain for BTC/ETH from Deribit so I can see all available strikes, expirations, and their implied volatilities.

**Why this priority**: This is the foundation - without options data, nothing else works. A single snapshot provides immediate value for manual analysis.

**Independent Test**: Can be tested by running a command that returns the options chain for BTC with IVs visible, verified against Deribit website.

**Acceptance Scenarios**:

1. **Given** the pipeline is configured with Deribit credentials, **When** I request the BTC options chain, **Then** I receive all active options with strike, expiry, IV, bid/ask, and Greeks within 10 seconds.
2. **Given** I request options for ETH, **When** the fetch completes, **Then** I receive both call and put options grouped by expiration.
3. **Given** Deribit is unreachable, **When** I request options data, **Then** I receive a clear error with retry suggestion.

---

### User Story 2 - Build IV Surface (Priority: P1)

As a quant researcher, I want to construct an implied volatility surface from options data so I can visualize and analyze volatility across strikes and expirations.

**Why this priority**: IV surface is the core derivative for all analytics - skew, term structure, and calibration depend on it.

**Independent Test**: Can be tested by fetching options chain and generating a 2D IV surface (strike x expiry) with interpolation.

**Acceptance Scenarios**:

1. **Given** options chain data, **When** I build the IV surface, **Then** I receive a structured grid with IV values for (moneyness, days-to-expiry) coordinates.
2. **Given** sparse strike data, **When** surface is constructed, **Then** missing values are interpolated using cubic splines.
3. **Given** the IV surface, **When** I query ATM IV at 30 days, **Then** I receive the interpolated value with confidence bounds.

---

### User Story 3 - Extract Volatility Metrics (Priority: P2)

As a trader, I want to extract key volatility metrics (ATM IV, skew, term structure) from the IV surface so I can use them as signals in my trading strategies.

**Why this priority**: Extracted metrics are the actionable signals - raw IV surface is informative but not directly tradeable.

**Independent Test**: Can be tested by computing skew and term structure from IV surface, comparing against known market conditions.

**Acceptance Scenarios**:

1. **Given** an IV surface, **When** I extract skew, **Then** I receive 25-delta put-call skew value (put IV minus call IV).
2. **Given** an IV surface, **When** I extract term structure, **Then** I receive IV values at standard tenors (1D, 7D, 30D, 90D).
3. **Given** skew is negative (puts expensive), **When** signal is generated, **Then** metric indicates elevated tail risk expectation.

---

### User Story 4 - Historical IV Data (Priority: P2)

As a researcher, I want to fetch historical IV data so I can backtest strategies using vol signals.

**Why this priority**: Backtesting requires historical data - without it, strategies cannot be validated.

**Independent Test**: Can be tested by fetching 30 days of historical ATM IV and verifying data completeness.

**Acceptance Scenarios**:

1. **Given** a date range, **When** I request historical IV, **Then** I receive daily ATM IV snapshots for that period.
2. **Given** historical data exists locally, **When** I request overlapping dates, **Then** only new data is fetched (incremental update).
3. **Given** historical IV data, **When** I query for a specific date, **Then** I receive the IV surface snapshot for that day.

---

### User Story 5 - Regime-Switching Heston Calibration (Priority: P3)

As a quant, I want to calibrate Heston model parameters from the IV surface with parameters that adapt to detected regime so I can price exotic options and generate vol forecasts.

**Why this priority**: Model calibration is advanced functionality - valuable but requires IV surface to be stable first.

**Independent Test**: Can be tested by calibrating Heston params from IV surface, validating fit via RMSE.

**Acceptance Scenarios**:

1. **Given** an IV surface, **When** I run Heston calibration, **Then** I receive parameters (kappa, theta, sigma, rho, v0) with calibration error.
2. **Given** regime state from RegimeEnsemble, **When** parameters are calibrated, **Then** separate parameter sets are maintained per regime.
3. **Given** calibrated model, **When** I price an option, **Then** price matches market within 5% for liquid strikes.

---

### User Story 6 - Real-Time IV Updates (Priority: P3)

As a live trader, I want real-time IV updates so I can react to vol changes during trading.

**Why this priority**: Real-time is enhancement over snapshot - requires stable foundation first.

**Independent Test**: Can be tested by subscribing to IV updates and verifying changes arrive within 5 seconds of market move.

**Acceptance Scenarios**:

1. **Given** subscription is active, **When** option prices change on Deribit, **Then** IV surface is updated within 5 seconds.
2. **Given** WebSocket connection drops, **When** reconnection occurs, **Then** full IV surface is refreshed.

---

### Edge Cases

- What happens when option has zero volume (no trades)? -> Use mid price if bid/ask exist, mark as illiquid if spread > 20%.
- What happens when IV cannot be computed (extreme OTM)? -> Use extrapolation from nearby strikes, flag as synthetic.
- What happens during expiration? -> Exclude expiring options from surface, rebuild with next cycle.
- How are American-style options handled? -> Deribit uses European-style, no adjustment needed.
- What if Heston calibration fails to converge? -> Use previous calibration, log warning, retry with different seed.

## Requirements *(mandatory)*

### Functional Requirements

**Data Fetching:**
- **FR-001**: System MUST fetch options chain from Deribit via CCXT for BTC and ETH.
- **FR-002**: System MUST extract strike, expiry, IV, bid, ask, last price, and Greeks for each option.
- **FR-003**: System MUST fetch historical options snapshots with configurable date range.
- **FR-004**: System MUST support incremental updates (fetch only new data since last fetch).

**IV Surface:**
- **FR-005**: System MUST construct IV surface as 2D grid (moneyness x days-to-expiry).
- **FR-006**: System MUST interpolate missing IV values using cubic spline interpolation.
- **FR-007**: System MUST support moneyness in multiple formats (strike/spot, log-moneyness, delta).

**Volatility Metrics:**
- **FR-008**: System MUST compute ATM implied volatility for each tenor.
- **FR-009**: System MUST compute 25-delta put-call skew.
- **FR-010**: System MUST compute term structure as IV curve across expirations.
- **FR-011**: System MUST compute risk-reversal (RR) and butterfly spread (BF) metrics.

**Model Calibration:**
- **FR-012**: System MUST calibrate Heston model parameters from IV surface.
- **FR-013**: System MUST support regime-switching parameters (P3 compliance).
- **FR-014**: System MUST report calibration RMSE and parameter confidence intervals.

**Integration:**
- **FR-015**: System MUST persist all data in Parquet format compatible with NautilusTrader catalog.
- **FR-016**: System MUST integrate with RegimeEnsemble for regime-aware calibration.
- **FR-017**: System MUST provide CLI interface for manual operations.

### Key Entities

- **OptionContract**: Represents a single option. Attributes: instrument_id, underlying, strike, expiry, option_type (call/put), settlement (cash).
- **OptionQuote**: Market data for an option. Attributes: timestamp, bid, ask, last, volume, open_interest, iv, delta, gamma, vega, theta.
- **IVSurface**: 2D volatility surface. Attributes: timestamp, underlying, moneyness_grid, tenor_grid, iv_matrix, interpolation_method.
- **VolMetrics**: Extracted volatility signals. Attributes: timestamp, atm_iv_30d, skew_25d, term_structure, risk_reversal, butterfly.
- **HestonParams**: Calibrated model parameters. Attributes: kappa (mean reversion), theta (long-term variance), sigma (vol of vol), rho (correlation), v0 (initial variance), regime_state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Options chain fetch completes within 10 seconds for all active BTC options.
- **SC-002**: IV surface construction completes within 2 seconds from options chain.
- **SC-003**: Heston calibration RMSE < 2% for ATM options, < 5% for OTM options.
- **SC-004**: Historical data fetch retrieves 30 days of daily snapshots in under 60 seconds.
- **SC-005**: Real-time IV updates arrive within 5 seconds of market price change.
- **SC-006**: Skew and term structure metrics match industry standard calculations (verified against vol analytics platforms).
- **SC-007**: System handles 1000 options in a single chain without memory issues.

## Scope

### In Scope

- Deribit BTC and ETH options
- Current options chain snapshot
- Historical options snapshots (daily)
- IV surface construction with interpolation
- ATM IV, skew, term structure extraction
- Heston model calibration (regime-aware)
- Parquet storage
- CLI interface

### Out of Scope

- Options execution/trading (use NautilusTrader adapter when available)
- Real-time Greeks computation (use static Greeks from exchange)
- Monte Carlo pricing (Heston gives analytical prices)
- SABR or other vol models (defer to future spec)
- Multi-exchange options aggregation (Deribit only for v1)

## Assumptions

- Deribit provides sufficient liquidity for IV calibration (BTC/ETH main expiries).
- CCXT supports Deribit options endpoints (verified: fetchOptionChain, fetchGreeks).
- European-style options only (Deribit standard).
- Greeks provided by exchange are accurate enough for analytics (not pricing).
- RegimeEnsemble (spec 036) provides regime state for switching parameters.

## Dependencies

- `scripts/ccxt_pipeline/` - Existing CCXT pipeline infrastructure
- `strategies/common/regime_detection/` - RegimeEnsemble for regime state
- NautilusTrader ParquetDataCatalog - Storage format
- CCXT >= 4.4.0 - Deribit options support

## Technical Notes

### CCXT Deribit Support (Verified)

```python
# Options chain
deribit = ccxt.deribit()
options = deribit.fetch_option_chain('BTC')  # All active options

# Individual option
ticker = deribit.fetch_ticker('BTC-27DEC24-100000-C')  # Specific option

# Greeks included in ticker response
# mark_iv, underlying_price, delta, gamma, vega, theta
```

### NautilusTrader Integration

- NT Deribit adapter is under construction
- Use Tardis integration for real-time (recommended)
- CCXT sufficient for historical/snapshot data

### Heston Calibration Approach

1. Extract market IVs from options chain
2. Detect current regime from RegimeEnsemble
3. Load regime-specific initial params (or defaults)
4. Minimize ||market_IV - model_IV||^2 using scipy.optimize
5. Store params indexed by regime state
6. P3 compliance: params are not fixed, they adapt to regime
