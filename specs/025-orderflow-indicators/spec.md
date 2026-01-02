# Feature Specification: Orderflow Indicators

**Feature Branch**: `025-orderflow-indicators`
**Created**: 2026-01-02
**Status**: Draft
**Input**: Implementation priority matrix - Phase 2 Orderflow

## User Scenarios & Testing *(mandatory)*

### User Story 1 - VPIN Toxicity Indicator (Priority: P1)

As a trader, I want to calculate Volume-Synchronized Probability of Informed Trading (VPIN) so that I can detect toxic order flow and reduce position size during high-toxicity periods.

**Why this priority**: Leading indicator of flash crashes. Directly impacts position sizing.

**Independent Test**: Can verify VPIN calculation against known flash crash events (shows elevated values).

**Acceptance Scenarios**:

1. **Given** tick/bar data with volume, **When** VPIN calculated, **Then** returns value 0.0-1.0
2. **Given** VPIN > 0.7, **When** toxicity queried, **Then** returns "high_toxicity"
3. **Given** normal market conditions, **When** VPIN calculated, **Then** value stays below 0.5
4. **Given** flash crash scenario (historical), **When** VPIN backtested, **Then** shows spike before crash

---

### User Story 2 - Hawkes Process Order Flow Imbalance (Priority: P2)

As a trader, I want to model order arrival as a self-exciting Hawkes process so that I can detect order flow clustering and momentum.

**Why this priority**: Captures temporal clustering of orders. Academic edge.

**Independent Test**: Can verify Hawkes intensity spikes correlate with price moves.

**Acceptance Scenarios**:

1. **Given** trade tick stream, **When** Hawkes intensity calculated, **Then** returns current intensity value
2. **Given** burst of buy orders, **When** intensity queried, **Then** shows elevated buy-side intensity
3. **Given** imbalance (buy_intensity >> sell_intensity), **When** OFI calculated, **Then** returns positive imbalance
4. **Given** mean-reverting conditions, **When** intensity decays, **Then** follows exponential decay

---

### Edge Cases

- What happens when tick data has gaps (missing ticks)?
- How to handle VPIN with very low volume periods?
- What if Hawkes process doesn't converge during fitting?
- How to handle bid/ask data unavailable (use close vs open heuristic)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate VPIN using volume buckets
- **FR-002**: System MUST support configurable bucket size (default: 50 trades)
- **FR-003**: System MUST classify trades as buy/sell (tick rule or bid/ask)
- **FR-004**: System MUST fit Hawkes process parameters online
- **FR-005**: System MUST calculate Order Flow Imbalance (OFI) from Hawkes
- **FR-006**: System MUST provide streaming updates (not just batch)
- **FR-007**: System MUST handle missing bid/ask with close-vs-open heuristic
- **FR-008**: System MUST integrate with Giller sizing (toxicity penalty)

### Key Entities

- **VPINBucket**: Volume bucket with buy/sell classification
- **ToxicityLevel**: Low (<0.3), Medium (0.3-0.7), High (>0.7)
- **HawkesState**: Current intensity, decay parameters, branching ratio
- **OrderFlowImbalance**: Normalized difference between buy/sell intensity

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: VPIN calculation latency <5ms per bucket
- **SC-002**: VPIN shows >0.7 correlation with subsequent volatility spikes
- **SC-003**: Hawkes process fitting converges in <1 second on 10K ticks
- **SC-004**: OFI correctly predicts short-term price direction >55% of time
- **SC-005**: All components have >80% test coverage
- **SC-006**: Works with both tick data and bar data (with heuristics)

## Technical Notes

### Dependencies

```bash
uv pip install tick  # Hawkes process library
# or custom implementation using scipy.optimize
```

### File Structure

```
strategies/common/orderflow/
├── __init__.py
├── vpin.py              # VPIN toxicity indicator
├── hawkes_ofi.py        # Hawkes process OFI
├── trade_classifier.py  # Buy/sell classification
└── orderflow_manager.py # Unified interface

tests/
├── test_vpin.py
├── test_hawkes_ofi.py
└── test_trade_classifier.py
```

### VPIN Algorithm

```python
def calculate_vpin(trades, bucket_size=50):
    """
    VPIN = |V_buy - V_sell| / (V_buy + V_sell)
    Calculated over rolling volume buckets
    """
    buckets = create_volume_buckets(trades, bucket_size)
    vpins = []
    for bucket in buckets:
        v_buy = sum(t.volume for t in bucket if t.is_buy)
        v_sell = sum(t.volume for t in bucket if not t.is_buy)
        vpin = abs(v_buy - v_sell) / (v_buy + v_sell + 1e-10)
        vpins.append(vpin)
    return np.mean(vpins[-50:])  # Rolling average
```

### References

- `docs/research/trading_ml_research_final_2026.md` (VPIN section)
- `docs/research/implementation_priority_matrix_2026.md`
- Easley, D., López de Prado, M., & O'Hara, M. (2012). "Flow Toxicity and Liquidity"
