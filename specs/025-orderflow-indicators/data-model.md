# Data Model: Orderflow Indicators (Spec 025)

**Feature Branch**: `025-orderflow-indicators`
**Created**: 2026-01-02

## Entity Diagram

```
┌─────────────────────┐     ┌──────────────────────┐
│   VPINIndicator     │     │    HawkesOFI         │
├─────────────────────┤     ├──────────────────────┤
│ - config: VPINConfig│     │ - config: HawkesConfig│
│ - buckets: list     │     │ - buy_times: list    │
│ - current_bucket    │     │ - sell_times: list   │
│ - value: float      │     │ - hawkes: HawkesExpKern│
└─────────┬───────────┘     └──────────┬───────────┘
          │                            │
          │    ┌───────────────────┐   │
          └───►│ OrderflowManager  │◄──┘
               ├───────────────────┤
               │ + toxicity: float │
               │ + ofi: float      │
               │ + update(bar)     │
               └─────────┬─────────┘
                         │
                         ▼
               ┌───────────────────┐
               │   GillerSizer     │
               │   (Spec 024)      │
               │ calculate(...,    │
               │   toxicity=...)   │
               └───────────────────┘
```

---

## Entities

### 1. VPINConfig

**Purpose**: Configuration for VPIN indicator.

```python
from pydantic import BaseModel, Field, field_validator

class VPINConfig(BaseModel):
    """Configuration for VPIN (Volume-Synchronized Probability of Informed Trading)."""

    bucket_size: float = Field(
        default=1000.0,
        gt=0,
        description="Volume per bucket (e.g., 1000 contracts)"
    )
    n_buckets: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Number of buckets for rolling VPIN"
    )
    classification_method: str = Field(
        default="tick_rule",
        description="Trade classification: 'tick_rule', 'bvc', 'close_vs_open'"
    )
    min_bucket_volume: float = Field(
        default=100.0,
        ge=0,
        description="Minimum volume to form a valid bucket"
    )

    @field_validator("classification_method")
    @classmethod
    def validate_classification(cls, v: str) -> str:
        valid = {"tick_rule", "bvc", "close_vs_open"}
        if v not in valid:
            raise ValueError(f"classification_method must be one of {valid}")
        return v

    model_config = {"frozen": True}
```

**Validation Rules**:
- `bucket_size` must be > 0
- `n_buckets` must be between 10 and 200
- `classification_method` must be one of allowed values

---

### 2. VPINBucket

**Purpose**: Single volume bucket for VPIN calculation.

```python
from dataclasses import dataclass

@dataclass
class VPINBucket:
    """A volume bucket for VPIN calculation."""

    volume_target: float       # Target volume for this bucket
    accumulated_volume: float  # Current accumulated volume
    buy_volume: float          # Buy-classified volume
    sell_volume: float         # Sell-classified volume
    start_time: int            # Bucket start timestamp (ns)
    end_time: int | None       # Bucket end timestamp (ns)

    @property
    def order_imbalance(self) -> float:
        """Calculate Order Imbalance (OI) for this bucket."""
        total = self.buy_volume + self.sell_volume
        if total <= 0:
            return 0.0
        return abs(self.buy_volume - self.sell_volume) / total

    @property
    def is_complete(self) -> bool:
        """Check if bucket has reached target volume."""
        return self.accumulated_volume >= self.volume_target
```

**State Transitions**:
1. `new` → Bucket created with volume_target
2. `filling` → Trades added, accumulated_volume increasing
3. `complete` → accumulated_volume >= volume_target, end_time set

---

### 3. ToxicityLevel (Enum)

**Purpose**: Categorical toxicity classification.

```python
from enum import Enum

class ToxicityLevel(Enum):
    """Toxicity level based on VPIN value."""

    LOW = "low"           # VPIN < 0.3
    MEDIUM = "medium"     # 0.3 <= VPIN < 0.7
    HIGH = "high"         # VPIN >= 0.7

    @classmethod
    def from_vpin(cls, vpin: float) -> "ToxicityLevel":
        """Convert VPIN value to toxicity level."""
        if vpin < 0.3:
            return cls.LOW
        elif vpin < 0.7:
            return cls.MEDIUM
        else:
            return cls.HIGH
```

---

### 4. HawkesConfig

**Purpose**: Configuration for Hawkes OFI indicator.

```python
class HawkesConfig(BaseModel):
    """Configuration for Hawkes process Order Flow Imbalance."""

    decay_rate: float = Field(
        default=1.0,
        gt=0,
        description="Exponential decay rate (β)"
    )
    lookback_ticks: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Number of ticks to keep in buffer"
    )
    refit_interval: int = Field(
        default=100,
        ge=10,
        description="Refit Hawkes model every N ticks"
    )
    use_fixed_params: bool = Field(
        default=False,
        description="Use fixed μ, α, β instead of online fitting"
    )
    fixed_baseline: float = Field(
        default=0.1,
        ge=0,
        description="Fixed baseline intensity μ (if use_fixed_params)"
    )
    fixed_excitation: float = Field(
        default=0.5,
        ge=0,
        lt=1,
        description="Fixed excitation α (if use_fixed_params, must be < decay for stationarity)"
    )

    @field_validator("fixed_excitation")
    @classmethod
    def validate_branching_ratio(cls, v: float, info) -> float:
        """Ensure branching ratio < 1 for stationarity."""
        # Branching ratio η = α/β < 1
        decay = info.data.get("decay_rate", 1.0)
        if v >= decay:
            raise ValueError(f"fixed_excitation ({v}) must be < decay_rate ({decay})")
        return v

    model_config = {"frozen": True}
```

---

### 5. HawkesState

**Purpose**: Current state of Hawkes process.

```python
@dataclass
class HawkesState:
    """Current state of Hawkes process for OFI."""

    buy_intensity: float      # Current λ_buy
    sell_intensity: float     # Current λ_sell
    baseline: tuple[float, float]  # (μ_buy, μ_sell)
    excitation: tuple[float, float]  # (α_buy, α_sell)
    decay: float              # β (shared)
    branching_ratio: float    # η = α/β
    last_fit_time: int        # Timestamp of last model fit (ns)
    ticks_since_fit: int      # Ticks since last fit

    @property
    def ofi(self) -> float:
        """Order Flow Imbalance = normalized intensity difference."""
        total = self.buy_intensity + self.sell_intensity
        if total <= 0:
            return 0.0
        return (self.buy_intensity - self.sell_intensity) / total
```

---

### 6. OrderflowConfig

**Purpose**: Unified configuration for orderflow manager.

```python
class OrderflowConfig(BaseModel):
    """Configuration for OrderflowManager."""

    vpin: VPINConfig = Field(default_factory=VPINConfig)
    hawkes: HawkesConfig = Field(default_factory=HawkesConfig)
    enable_vpin: bool = Field(default=True)
    enable_hawkes: bool = Field(default=True)

    model_config = {"frozen": True}
```

---

### 7. TradeClassification

**Purpose**: Result of trade direction classification.

```python
@dataclass
class TradeClassification:
    """Result of classifying a trade as buy or sell."""

    side: int              # 1 for buy, -1 for sell, 0 for unknown
    volume: float          # Trade volume
    price: float           # Trade price
    timestamp: int         # Trade timestamp (ns)
    method: str            # Classification method used
    confidence: float      # Confidence in classification [0, 1]
```

---

## Relationships

```
OrderflowConfig (1) ──────► VPINConfig (1)
                └──────────► HawkesConfig (1)

VPINIndicator (1) ────────► VPINBucket (many)
                 └────────► VPINConfig (1)

HawkesOFI (1) ────────────► HawkesState (1)
             └────────────► HawkesConfig (1)

OrderflowManager (1) ─────► VPINIndicator (1)
                    └─────► HawkesOFI (1)
                    └─────► OrderflowConfig (1)

ToxicityLevel ◄───── derived from VPINIndicator.value
```

---

## State Diagram: VPINIndicator

```
                    ┌─────────────┐
                    │   IDLE      │
                    │ (no data)   │
                    └──────┬──────┘
                           │ handle_bar()
                           ▼
                    ┌─────────────┐
           ┌───────►│  FILLING    │◄───────┐
           │        │ (bucket <   │        │
           │        │  target)    │        │
           │        └──────┬──────┘        │
           │               │ bucket.is_complete
           │               ▼               │
           │        ┌─────────────┐        │
           │        │  COMPLETE   │        │
           │        │ (recalculate│        │
           │        │  VPIN)      │────────┘
           │        └──────┬──────┘  new bucket
           │               │
           │               │ n_buckets >= config.n_buckets
           │               ▼
           │        ┌─────────────┐
           └────────│   READY     │
                    │ (VPIN valid)│
                    └─────────────┘
```

---

## Integration Points

### Input: NautilusTrader Bar

```python
from nautilus_trader.model.data import Bar

def handle_bar(self, bar: Bar) -> None:
    """Process a bar and update indicators."""
    # Extract trade info
    price = float(bar.close)
    volume = float(bar.volume)
    timestamp = bar.ts_event

    # Classify direction
    classification = self.classifier.classify(bar)

    # Update VPIN
    self.vpin.update(classification)

    # Update Hawkes
    self.hawkes.update(classification)
```

### Output: To GillerSizer

```python
# GillerSizer already accepts toxicity parameter
position_size = giller_sizer.calculate(
    signal=signal_strength,
    regime_weight=regime_manager.regime_weight,
    toxicity=orderflow_manager.toxicity  # From VPIN
)
```
