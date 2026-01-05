# Action Items: Adaptive Control Framework

## Prima di Paper Trading (Day 0)

| Item | Owner | Effort | File | Line |
|------|-------|--------|------|------|
| [x] Fix `update_strategy_performance()` → `record_strategy_pnl()` | Dev | 30m | alpha_evolve_bridge.py | 384 |
| [ ] Fix `update()` signature mismatch | Dev | 30m | alpha_evolve_bridge.py | 411 |
| [ ] Add NaN input guards to MetaController.update() | Dev | 15m | meta_controller.py | 240+ |
| [ ] Add NaN guards to SystemHealthMonitor.update() | Dev | 15m | system_health.py | 100+ |

**Total: ~1.5 hours**

---

## Durante Paper Trading (Week 1)

| Item | Priority | Effort | Notes |
|------|----------|--------|-------|
| [ ] Implement CSRC covariance penalty | HIGH | 8h | particle_portfolio.py - add cov matrix |
| [ ] Implement ADTS regime-adaptive decay | HIGH | 6h | particle_portfolio.py - decay = f(volatility) |
| [ ] Add fallback to uniform weights when all particles zero | HIGH | 1h | particle_portfolio.py:155-160 |
| [ ] Add floor to Thompson stats (prevent decay to zero) | MED | 1h | particle_portfolio.py:331-334 |
| [ ] Add explicit logging for UNKNOWN regime | MED | 30m | meta_controller.py |
| [ ] Wrap lazy init in try/except | MED | 1h | meta_controller.py:162-188 |

**Total: ~17.5 hours**

---

## Durante Paper Trading (Week 2-3)

| Item | Priority | Effort | Notes |
|------|----------|--------|-------|
| [ ] Add Level 3 Strategic Controller | HIGH | 12h | New module: strategic_controller.py |
| [ ] Integrate Walk-Forward with Meta-Portfolio | MED | 8h | Connect scripts/alpha_evolve/walk_forward/ |
| [ ] Add Transaction Cost Model | MED | 6h | sops_sizing.py - Kyle's Lambda |
| [ ] Implement Kelly at Portfolio Level | LOW | 4h | meta_portfolio.py optional layer |

**Total: ~30 hours**

---

## Post Paper Trading (Se Skill > Luck)

| Item | Priority | Effort | Notes |
|------|----------|--------|-------|
| [ ] Add BOCD for real-time regime | MED | 8h | Adams & MacKay 2007 |
| [ ] MAML Meta-Learning integration | LOW | 16h | Only if evolution too slow |
| [ ] Validate experimental modules vs baseline | LOW | 8h | FlowPhysics, VibrationAnalysis |
| [ ] Make PID gains adaptive | LOW | 4h | Auto-tune based on response |
| [ ] Regime threshold auto-calibration | LOW | 6h | Data-driven thresholds |

**Total: ~42 hours**

---

## Quick Reference: Files to Modify

### Day 0 (Critical)
```
strategies/common/adaptive_control/alpha_evolve_bridge.py  # API fix
strategies/common/adaptive_control/meta_controller.py       # NaN guard
strategies/common/adaptive_control/system_health.py         # NaN guard
```

### Week 1-2
```
strategies/common/adaptive_control/particle_portfolio.py   # CSRC, ADTS, fallbacks
strategies/common/adaptive_control/sops_sizing.py          # Transaction costs
```

### Week 3+
```
strategies/common/adaptive_control/strategic_controller.py # NEW FILE
scripts/alpha_evolve/walk_forward/validator.py             # Integration
```

---

## Validation Checklist

### Before Paper Trading
- [ ] All tests pass: `uv run pytest tests/adaptive_control/ -v`
- [ ] No runtime errors in smoke test: `python -c "from strategies.common.adaptive_control import *"`
- [ ] API mismatch fixed and tested

### After Week 1
- [ ] No crashes in paper trading logs
- [ ] UNKNOWN regime < 20% of time
- [ ] Correlation concentration logged and analyzed
- [ ] DSR trending positive (skill > luck)

### After Week 2
- [ ] CSRC implemented and active
- [ ] ADTS decay responsive to volatility
- [ ] Position sizes scaling appropriately
