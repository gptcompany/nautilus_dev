#!/usr/bin/env python3
"""
ORDER FLOW & VOLUME PROFILE PRICE TARGETS
==========================================
Implementazione di metodi avanzati per calcolo target basati su:
- Volume Profile (POC, VAH, VAL, HVN, LVN)
- VWAP con Standard Deviation Bands
- Delta e Order Flow (se dati disponibili)
- Market Profile concepts

Questi metodi sono più rigorosi perché basati su dati reali di volume
e transazioni, non solo su pattern geometrici di prezzo.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class VolumeProfileResult:
    """Risultato analisi Volume Profile"""

    poc: float  # Point of Control
    vah: float  # Value Area High
    val: float  # Value Area Low
    hvn: List[float]  # High Volume Nodes
    lvn: List[float]  # Low Volume Nodes
    va_percent: float  # Percentuale Value Area


@dataclass
class VWAPResult:
    """Risultato calcolo VWAP"""

    vwap: float
    std: float
    bands: Dict[str, float]


class VolumeProfileAnalyzer:
    """
    Analizzatore di Volume Profile
    Calcola POC, Value Area, HVN, LVN
    """

    def __init__(self, df: pd.DataFrame, num_bins: int = 50):
        """
        Args:
            df: DataFrame con columns 'high', 'low', 'close', 'volume'
            num_bins: Numero di livelli di prezzo per il profilo
        """
        self.df = df
        self.num_bins = num_bins
        self.profile = None
        self.result = None

    def calculate(self, va_percent: float = 70.0) -> VolumeProfileResult:
        """
        Calcola il Volume Profile completo

        Args:
            va_percent: Percentuale per Value Area (default 70%)
        """
        price_min = self.df["low"].min()
        price_max = self.df["high"].max()

        # Crea bins di prezzo
        bins = np.linspace(price_min, price_max, self.num_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        bin_width = bins[1] - bins[0]

        # Calcola volume per ogni bin
        volume_profile = np.zeros(self.num_bins)

        for _, row in self.df.iterrows():
            bar_low = row["low"]
            bar_high = row["high"]
            bar_volume = row["volume"]
            bar_range = bar_high - bar_low

            if bar_range < 0.0001:
                # Candela doji - tutto volume a un livello
                idx = np.searchsorted(bins, row["close"]) - 1
                idx = max(0, min(idx, self.num_bins - 1))
                volume_profile[idx] += bar_volume
            else:
                # Distribuisci volume nel range della candela
                for i in range(self.num_bins):
                    bin_low = bins[i]
                    bin_high = bins[i + 1]

                    # Calcola overlap
                    overlap_low = max(bar_low, bin_low)
                    overlap_high = min(bar_high, bin_high)

                    if overlap_high > overlap_low:
                        overlap_ratio = (overlap_high - overlap_low) / bar_range
                        volume_profile[i] += bar_volume * overlap_ratio

        self.profile = dict(zip(bin_centers, volume_profile))

        # POC - Point of Control
        poc_idx = np.argmax(volume_profile)
        poc = bin_centers[poc_idx]

        # Value Area (va_percent del volume totale)
        total_volume = volume_profile.sum()
        target_volume = total_volume * (va_percent / 100.0)

        # Espandi da POC
        va_indices = {poc_idx}
        current_volume = volume_profile[poc_idx]
        low_idx = poc_idx - 1
        high_idx = poc_idx + 1

        while current_volume < target_volume:
            low_vol = volume_profile[low_idx] if low_idx >= 0 else -1
            high_vol = volume_profile[high_idx] if high_idx < self.num_bins else -1

            if low_vol < 0 and high_vol < 0:
                break

            if low_vol >= high_vol:
                va_indices.add(low_idx)
                current_volume += low_vol
                low_idx -= 1
            else:
                va_indices.add(high_idx)
                current_volume += high_vol
                high_idx += 1

        val = bin_centers[min(va_indices)]
        vah = bin_centers[max(va_indices)]

        # HVN e LVN
        mean_vol = np.mean(volume_profile)
        std_vol = np.std(volume_profile)

        hvn_mask = volume_profile > (mean_vol + 0.5 * std_vol)
        lvn_mask = volume_profile < (mean_vol - 0.3 * std_vol)

        hvn = list(bin_centers[hvn_mask])
        lvn = list(bin_centers[lvn_mask])

        self.result = VolumeProfileResult(
            poc=poc, vah=vah, val=val, hvn=hvn, lvn=lvn, va_percent=va_percent
        )

        return self.result

    def get_targets(self, current_price: float, direction: str = "long") -> List[Dict]:
        """
        Genera target basati sul Volume Profile
        """
        if self.result is None:
            self.calculate()

        r = self.result
        targets = []

        if direction == "long":
            # Target sopra il prezzo corrente
            if r.poc > current_price:
                targets.append(
                    {
                        "level": r.poc,
                        "type": "POC",
                        "strength": "very_strong",
                        "description": "Point of Control - massimo volume",
                    }
                )

            if r.vah > current_price:
                targets.append(
                    {
                        "level": r.vah,
                        "type": "VAH",
                        "strength": "strong",
                        "description": "Value Area High",
                    }
                )

            for hvn in r.hvn:
                if hvn > current_price:
                    targets.append(
                        {
                            "level": hvn,
                            "type": "HVN",
                            "strength": "medium",
                            "description": "High Volume Node - resistenza",
                        }
                    )

        else:  # short
            if r.poc < current_price:
                targets.append(
                    {
                        "level": r.poc,
                        "type": "POC",
                        "strength": "very_strong",
                        "description": "Point of Control - massimo volume",
                    }
                )

            if r.val < current_price:
                targets.append(
                    {
                        "level": r.val,
                        "type": "VAL",
                        "strength": "strong",
                        "description": "Value Area Low",
                    }
                )

            for hvn in r.hvn:
                if hvn < current_price:
                    targets.append(
                        {
                            "level": hvn,
                            "type": "HVN",
                            "strength": "medium",
                            "description": "High Volume Node - supporto",
                        }
                    )

        # Ordina per distanza
        targets.sort(key=lambda x: abs(x["level"] - current_price))

        return targets


class VWAPCalculator:
    """
    Calcola VWAP con Standard Deviation Bands
    """

    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: DataFrame con columns 'high', 'low', 'close', 'volume'
        """
        self.df = df.copy()
        self.result = None

    def calculate(self, anchor_index: int = 0) -> VWAPResult:
        """
        Calcola VWAP e bande di deviazione standard

        Args:
            anchor_index: Indice da cui iniziare il calcolo (0 = inizio)
        """
        df = self.df.iloc[anchor_index:].copy()

        # Typical Price
        df["tp"] = (df["high"] + df["low"] + df["close"]) / 3

        # VWAP
        df["tp_vol"] = df["tp"] * df["volume"]
        df["cum_tp_vol"] = df["tp_vol"].cumsum()
        df["cum_vol"] = df["volume"].cumsum()
        df["vwap"] = df["cum_tp_vol"] / df["cum_vol"]

        # Standard Deviation
        df["tp_sq_vol"] = (df["tp"] ** 2) * df["volume"]
        df["cum_tp_sq_vol"] = df["tp_sq_vol"].cumsum()
        df["variance"] = (df["cum_tp_sq_vol"] / df["cum_vol"]) - (df["vwap"] ** 2)
        df["std"] = np.sqrt(np.maximum(df["variance"], 0))

        # Valori correnti
        vwap = df["vwap"].iloc[-1]
        std = df["std"].iloc[-1]

        bands = {
            "upper_1": vwap + std,
            "upper_2": vwap + 2 * std,
            "upper_3": vwap + 3 * std,
            "lower_1": vwap - std,
            "lower_2": vwap - 2 * std,
            "lower_3": vwap - 3 * std,
        }

        self.result = VWAPResult(vwap=vwap, std=std, bands=bands)
        return self.result

    def get_targets(self, current_price: float, direction: str = "long") -> List[Dict]:
        """
        Genera target basati su VWAP bands
        """
        if self.result is None:
            self.calculate()

        r = self.result
        targets = []

        # Mean reversion target
        if direction == "long" and current_price < r.vwap:
            targets.append(
                {
                    "level": r.vwap,
                    "type": "VWAP",
                    "probability": "70%",
                    "description": "Return to VWAP (fair value)",
                }
            )
        elif direction == "short" and current_price > r.vwap:
            targets.append(
                {
                    "level": r.vwap,
                    "type": "VWAP",
                    "probability": "70%",
                    "description": "Return to VWAP (fair value)",
                }
            )

        if direction == "long":
            targets.extend(
                [
                    {
                        "level": r.bands["upper_1"],
                        "type": "VWAP +1σ",
                        "probability": "68%",
                        "description": "Prima deviazione standard",
                    },
                    {
                        "level": r.bands["upper_2"],
                        "type": "VWAP +2σ",
                        "probability": "95%",
                        "description": "Seconda deviazione (estensione)",
                    },
                    {
                        "level": r.bands["upper_3"],
                        "type": "VWAP +3σ",
                        "probability": "99%",
                        "description": "Estremo statistico",
                    },
                ]
            )
        else:
            targets.extend(
                [
                    {
                        "level": r.bands["lower_1"],
                        "type": "VWAP -1σ",
                        "probability": "68%",
                        "description": "Prima deviazione standard",
                    },
                    {
                        "level": r.bands["lower_2"],
                        "type": "VWAP -2σ",
                        "probability": "95%",
                        "description": "Seconda deviazione (estensione)",
                    },
                    {
                        "level": r.bands["lower_3"],
                        "type": "VWAP -3σ",
                        "probability": "99%",
                        "description": "Estremo statistico",
                    },
                ]
            )

        # Filtra solo target nella direzione corretta
        if direction == "long":
            targets = [t for t in targets if t["level"] > current_price]
        else:
            targets = [t for t in targets if t["level"] < current_price]

        # Ordina per distanza
        targets.sort(key=lambda x: abs(x["level"] - current_price))

        return targets


class MarketProfileTargets:
    """
    Calcola target basati su concetti Market Profile
    - Initial Balance extensions
    - 80% Rule
    - Poor Highs/Lows
    """

    @staticmethod
    def initial_balance_targets(
        ib_high: float, ib_low: float, direction: str = "long"
    ) -> Dict[str, float]:
        """
        Target da Initial Balance (prime 1-2 ore)

        Args:
            ib_high: Massimo dell'Initial Balance
            ib_low: Minimo dell'Initial Balance
        """
        ib_range = ib_high - ib_low

        if direction == "long":
            return {
                "target_0.5x": ib_high + ib_range * 0.5,
                "target_1.0x": ib_high + ib_range * 1.0,
                "target_1.5x": ib_high + ib_range * 1.5,
                "target_2.0x": ib_high + ib_range * 2.0,
            }
        else:
            return {
                "target_0.5x": ib_low - ib_range * 0.5,
                "target_1.0x": ib_low - ib_range * 1.0,
                "target_1.5x": ib_low - ib_range * 1.5,
                "target_2.0x": ib_low - ib_range * 2.0,
            }

    @staticmethod
    def eighty_percent_rule(
        prev_vah: float, prev_val: float, current_price: float
    ) -> Optional[Dict]:
        """
        80% Rule: Se il prezzo entra nella VA precedente,
        80% probabilità di raggiungere l'altro estremo

        Args:
            prev_vah: Value Area High del giorno precedente
            prev_val: Value Area Low del giorno precedente
            current_price: Prezzo attuale
        """
        # Verifica se siamo entrati nella VA
        if prev_val <= current_price <= prev_vah:
            # Determina da quale lato siamo entrati
            mid_va = (prev_vah + prev_val) / 2

            if current_price < mid_va:
                return {
                    "entry_side": "bottom",
                    "target": prev_vah,
                    "probability": "80%",
                    "description": "Entrato da VAL, target VAH",
                }
            else:
                return {
                    "entry_side": "top",
                    "target": prev_val,
                    "probability": "80%",
                    "description": "Entrato da VAH, target VAL",
                }

        return None


class OrderFlowTargetCalculator:
    """
    Classe principale che combina tutti i metodi
    """

    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: DataFrame con OHLCV data
        """
        self.df = df
        self.volume_profile = VolumeProfileAnalyzer(df)
        self.vwap = VWAPCalculator(df)

    def get_all_targets(self, current_price: float, direction: str = "long") -> Dict:
        """
        Calcola tutti i target da tutti i metodi
        """
        # Calcola profili
        vp_result = self.volume_profile.calculate()
        vwap_result = self.vwap.calculate()

        # Ottieni target
        vp_targets = self.volume_profile.get_targets(current_price, direction)
        vwap_targets = self.vwap.get_targets(current_price, direction)

        # Combina
        all_targets = vp_targets + vwap_targets

        # Ordina per distanza
        all_targets.sort(key=lambda x: abs(x["level"] - current_price))

        # Trova confluenze
        confluences = self._find_confluences(all_targets, tolerance=0.005)

        return {
            "volume_profile": vp_result,
            "vwap": vwap_result,
            "all_targets": all_targets,
            "confluences": confluences,
            "primary_target": confluences[0]
            if confluences
            else (all_targets[0] if all_targets else None),
        }

    def _find_confluences(self, targets: List[Dict], tolerance: float = 0.005) -> List[Dict]:
        """
        Trova livelli dove più target convergono
        """
        if len(targets) < 2:
            return []

        levels = [t["level"] for t in targets]
        levels.sort()

        confluences = []
        i = 0

        while i < len(levels):
            cluster = [levels[i]]
            j = i + 1

            while j < len(levels):
                if abs(levels[j] - cluster[-1]) / cluster[-1] <= tolerance:
                    cluster.append(levels[j])
                    j += 1
                else:
                    break

            if len(cluster) >= 2:
                mean_level = np.mean(cluster)
                methods = [
                    t["type"]
                    for t in targets
                    if any(abs(t["level"] - c) / c <= tolerance for c in cluster)
                ]

                confluences.append(
                    {
                        "level": mean_level,
                        "strength": len(cluster),
                        "methods": methods,
                        "description": f"Confluenza {len(cluster)} metodi",
                    }
                )

            i = j

        confluences.sort(key=lambda x: x["strength"], reverse=True)
        return confluences


# ========== FUNZIONI RAPIDE ==========


def quick_vwap_targets(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float],
    current_price: float,
    direction: str = "long",
) -> Dict:
    """
    Calcolo rapido VWAP targets da liste
    """
    df = pd.DataFrame({"high": highs, "low": lows, "close": closes, "volume": volumes})

    calc = VWAPCalculator(df)
    result = calc.calculate()
    targets = calc.get_targets(current_price, direction)

    return {"vwap": result.vwap, "std": result.std, "bands": result.bands, "targets": targets}


def quick_volume_profile_targets(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float],
    current_price: float,
    direction: str = "long",
) -> Dict:
    """
    Calcolo rapido Volume Profile targets da liste
    """
    df = pd.DataFrame({"high": highs, "low": lows, "close": closes, "volume": volumes})

    analyzer = VolumeProfileAnalyzer(df)
    result = analyzer.calculate()
    targets = analyzer.get_targets(current_price, direction)

    return {
        "poc": result.poc,
        "vah": result.vah,
        "val": result.val,
        "hvn": result.hvn,
        "lvn": result.lvn,
        "targets": targets,
    }


# ========== ESEMPIO D'USO ==========

if __name__ == "__main__":
    # Genera dati di esempio
    np.random.seed(42)
    n = 100

    # Simula dati OHLCV
    base_price = 100
    returns = np.random.normal(0, 0.02, n)
    prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame(
        {
            "open": prices,
            "high": prices * (1 + np.random.uniform(0, 0.01, n)),
            "low": prices * (1 - np.random.uniform(0, 0.01, n)),
            "close": prices * (1 + np.random.normal(0, 0.005, n)),
            "volume": np.random.uniform(1000, 5000, n),
        }
    )

    current_price = df["close"].iloc[-1]

    print("=" * 60)
    print("ORDER FLOW TARGETS - ESEMPIO")
    print("=" * 60)
    print(f"\nPrezzo corrente: ${current_price:.2f}")

    # Volume Profile
    print("\n--- VOLUME PROFILE ---")
    vp = VolumeProfileAnalyzer(df)
    vp_result = vp.calculate()
    print(f"POC: ${vp_result.poc:.2f}")
    print(f"VAH: ${vp_result.vah:.2f}")
    print(f"VAL: ${vp_result.val:.2f}")
    print(f"HVN: {[f'${x:.2f}' for x in vp_result.hvn[:3]]}")
    print(f"LVN: {[f'${x:.2f}' for x in vp_result.lvn[:3]]}")

    # VWAP
    print("\n--- VWAP BANDS ---")
    vwap = VWAPCalculator(df)
    vwap_result = vwap.calculate()
    print(f"VWAP: ${vwap_result.vwap:.2f}")
    print(f"StdDev: ${vwap_result.std:.2f}")
    print(f"+1σ: ${vwap_result.bands['upper_1']:.2f}")
    print(f"+2σ: ${vwap_result.bands['upper_2']:.2f}")
    print(f"-1σ: ${vwap_result.bands['lower_1']:.2f}")
    print(f"-2σ: ${vwap_result.bands['lower_2']:.2f}")

    # Target combinati
    print("\n--- TARGET COMBINATI (LONG) ---")
    calculator = OrderFlowTargetCalculator(df)
    results = calculator.get_all_targets(current_price, "long")

    print("\nTarget per priorità:")
    for i, t in enumerate(results["all_targets"][:5], 1):
        print(f"  {i}. {t['type']}: ${t['level']:.2f}")

    if results["confluences"]:
        print("\nConfluenze trovate:")
        for c in results["confluences"][:3]:
            print(f"  ${c['level']:.2f} ({c['strength']} metodi: {', '.join(c['methods'])})")

    # Initial Balance example
    print("\n--- INITIAL BALANCE TARGETS ---")
    ib_high = df["high"].iloc[:10].max()
    ib_low = df["low"].iloc[:10].min()
    ib_targets = MarketProfileTargets.initial_balance_targets(ib_high, ib_low, "long")
    print(f"IB Range: ${ib_low:.2f} - ${ib_high:.2f}")
    for name, level in ib_targets.items():
        print(f"  {name}: ${level:.2f}")

    print("\n" + "=" * 60)
    print("Script pronto per importazione:")
    print("from orderflow_targets import OrderFlowTargetCalculator")
    print("=" * 60)
