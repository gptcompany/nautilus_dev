#!/usr/bin/env python3
"""
PRICE TARGET CALCULATOR
=======================
Implementazione di metodi matematici per calcolo target di prezzo
Alternative al Point & Figure basate su statistica e geometria

Metodi implementati:
1. Point & Figure (senza grafico)
2. ATR Projection
3. Measured Move (AB=CD)
4. Fibonacci Extensions
5. Standard Deviation Projection
6. Volatility/Range Based
7. Composite (multi-method confluence)

Autore: Estratto da ricerca metodologica
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


@dataclass
class TargetResult:
    """Risultato di un calcolo target"""
    method: str
    level: float
    confidence: str  # 'low', 'medium', 'high'
    description: str


class PriceTargetCalculator:
    """
    Calcolatore di target di prezzo multi-metodo
    """
    
    # Livelli Fibonacci standard
    FIB_LEVELS = {
        'fib_100': 1.000,
        'fib_127': 1.272,
        'fib_162': 1.618,  # Golden Ratio
        'fib_200': 2.000,
        'fib_262': 2.618,
        'fib_424': 4.236
    }
    
    def __init__(self, df: pd.DataFrame = None):
        """
        Args:
            df: DataFrame con colonne 'open', 'high', 'low', 'close', 'volume' (opzionale)
        """
        self.df = df
        
    def calculate_atr(self, period: int = 14) -> float:
        """Calcola Average True Range"""
        if self.df is None:
            raise ValueError("DataFrame non fornito")
            
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr
    
    def calculate_std(self, period: int = 20) -> float:
        """Calcola Standard Deviation dei prezzi"""
        if self.df is None:
            raise ValueError("DataFrame non fornito")
        return self.df['close'].rolling(window=period).std().iloc[-1]
    
    # ========== METODO 1: POINT & FIGURE (SENZA GRAFICO) ==========
    
    def pnf_target(self, 
                   box_size: float = None, 
                   reversal: int = 3,
                   direction: str = 'up') -> Dict[str, float]:
        """
        Calcola target P&F senza costruire il grafico
        
        Args:
            box_size: Dimensione del box (se None, usa 1% del prezzo medio)
            reversal: Numero di box per inversione
            direction: 'up' o 'down'
        
        Returns:
            Dict con 'columns', 'cause', 'target'
        """
        if self.df is None:
            raise ValueError("DataFrame non fornito")
        
        # Auto box size
        if box_size is None:
            box_size = self.df['close'].mean() * 0.01
        
        # Conta le colonne (inversioni significative)
        closes = self.df['close'].values
        columns = 0
        current_direction = None
        
        for i in range(1, len(closes)):
            move = closes[i] - closes[i-1]
            boxes_moved = abs(move) / box_size
            
            if boxes_moved >= reversal:
                new_direction = 1 if move > 0 else -1
                if new_direction != current_direction:
                    columns += 1
                    current_direction = new_direction
        
        # Calcola cause
        range_high = self.df['high'].max()
        range_low = self.df['low'].min()
        cause = columns * box_size * reversal
        
        if direction == 'up':
            target = range_low + cause
        else:
            target = range_high - cause
        
        return {
            'columns': columns,
            'box_size': box_size,
            'reversal': reversal,
            'cause': cause,
            'range_high': range_high,
            'range_low': range_low,
            'target': target,
            'method': 'P&F Count'
        }
    
    def pnf_vertical_count(self, 
                          column_length: int, 
                          box_size: float,
                          reference_price: float,
                          reversal: int = 3,
                          direction: str = 'up') -> float:
        """
        P&F Vertical Count
        
        Formula: Target = Column_Length × Box_Size × Reversal + Reference
        
        Args:
            column_length: Numero di box nella colonna di breakout
            box_size: Dimensione del box
            reference_price: Prezzo di riferimento (minimo per up, massimo per down)
            reversal: Fattore di reversal (tipicamente 3)
            direction: 'up' o 'down'
        """
        extension = column_length * box_size * reversal
        
        if direction == 'up':
            return reference_price + extension
        else:
            return reference_price - extension
    
    def pnf_horizontal_count(self,
                            num_columns: int,
                            box_size: float,
                            range_low: float,
                            range_high: float,
                            reversal: int = 3,
                            direction: str = 'up') -> float:
        """
        P&F Horizontal Count (Wyckoff)
        
        Formula UP: Target = (Columns × Box × Reversal) + Range_Low
        Formula DOWN: Target = Range_High - (Columns × Box × Reversal)
        """
        cause = num_columns * box_size * reversal
        
        if direction == 'up':
            return range_low + cause
        else:
            return range_high - cause
    
    # ========== METODO 2: ATR PROJECTION ==========
    
    def atr_targets(self, 
                    entry_price: float,
                    atr: float = None,
                    period: int = 14,
                    direction: str = 'up',
                    multipliers: List[float] = [1.0, 1.5, 2.0, 3.0]) -> Dict[str, float]:
        """
        Target basati su multipli di ATR
        
        Args:
            entry_price: Prezzo di entrata
            atr: ATR (se None, calcola dal DataFrame)
            period: Periodo per calcolo ATR
            direction: 'up' o 'down'
            multipliers: Lista di moltiplicatori ATR
        """
        if atr is None:
            atr = self.calculate_atr(period)
        
        targets = {}
        for mult in multipliers:
            key = f'atr_{mult}x'
            if direction == 'up':
                targets[key] = entry_price + (atr * mult)
            else:
                targets[key] = entry_price - (atr * mult)
        
        targets['atr_value'] = atr
        targets['method'] = 'ATR Projection'
        
        return targets
    
    def atr_probability_targets(self,
                               entry_price: float,
                               atr: float,
                               direction: str = 'up') -> Dict[str, Dict]:
        """
        Target ATR con probabilità associate (distribuzione normale)
        
        1 ATR = 68.27% probabilità
        2 ATR = 95.45% probabilità  
        3 ATR = 99.73% probabilità
        """
        probabilities = {
            1.0: 0.6827,
            2.0: 0.9545,
            3.0: 0.9973
        }
        
        targets = {}
        for mult, prob in probabilities.items():
            if direction == 'up':
                level = entry_price + (atr * mult)
            else:
                level = entry_price - (atr * mult)
            
            targets[f'{mult}_std'] = {
                'level': level,
                'probability': prob,
                'description': f'{prob*100:.1f}% del movimento entro questo livello'
            }
        
        return targets
    
    # ========== METODO 3: MEASURED MOVE (AB=CD) ==========
    
    def measured_move(self,
                     point_a: float,
                     point_b: float,
                     point_c: float,
                     extensions: List[float] = [1.0, 1.272, 1.618]) -> Dict[str, float]:
        """
        Measured Move / AB=CD Pattern
        
        Formula: Target = C + (B - A) × Extension
        
        Args:
            point_a: Inizio primo impulso
            point_b: Fine primo impulso
            point_c: Fine ritracciamento
            extensions: Lista di estensioni da calcolare
        """
        move = point_b - point_a  # Può essere positivo o negativo
        
        targets = {
            'point_a': point_a,
            'point_b': point_b,
            'point_c': point_c,
            'initial_move': abs(move),
            'method': 'Measured Move'
        }
        
        for ext in extensions:
            key = f'mm_{int(ext*100)}%'
            targets[key] = point_c + (move * ext)
        
        return targets
    
    # ========== METODO 4: FIBONACCI EXTENSIONS ==========
    
    def fibonacci_extensions(self,
                            swing_low: float,
                            swing_high: float,
                            retracement_end: float,
                            direction: str = 'up') -> Dict[str, float]:
        """
        Fibonacci Extensions (3 punti)
        
        Args:
            swing_low: Minimo dello swing
            swing_high: Massimo dello swing
            retracement_end: Fine del ritracciamento
            direction: 'up' o 'down'
        """
        move = swing_high - swing_low
        
        targets = {
            'swing_low': swing_low,
            'swing_high': swing_high,
            'retracement': retracement_end,
            'move_size': move,
            'method': 'Fibonacci Extensions'
        }
        
        for name, ratio in self.FIB_LEVELS.items():
            if direction == 'up':
                targets[name] = retracement_end + (move * ratio)
            else:
                targets[name] = retracement_end - (move * ratio)
        
        return targets
    
    def fibonacci_simple(self,
                        start_price: float,
                        end_price: float) -> Dict[str, float]:
        """
        Fibonacci retracement e extension semplici (2 punti)
        """
        diff = end_price - start_price
        
        return {
            # Retracements (per pullback)
            'ret_236': end_price - diff * 0.236,
            'ret_382': end_price - diff * 0.382,
            'ret_500': end_price - diff * 0.500,
            'ret_618': end_price - diff * 0.618,
            'ret_786': end_price - diff * 0.786,
            # Extensions (per target)
            'ext_127': end_price + diff * 0.272,
            'ext_162': end_price + diff * 0.618,
            'ext_200': end_price + diff * 1.000,
            'ext_262': end_price + diff * 1.618,
        }
    
    # ========== METODO 5: STANDARD DEVIATION ==========
    
    def std_deviation_targets(self,
                             entry_price: float,
                             std: float = None,
                             period: int = 20,
                             multipliers: List[float] = [1, 2, 2.5, 3, 4]) -> Dict[str, Dict]:
        """
        Standard Deviation Projection (ICT/SMC style)
        """
        if std is None:
            std = self.calculate_std(period)
        
        targets = {'std_value': std, 'method': 'StdDev Projection'}
        
        for mult in multipliers:
            targets[f'std_{mult}'] = {
                'upper': entry_price + (std * mult),
                'lower': entry_price - (std * mult)
            }
        
        return targets
    
    def std_channel_targets(self,
                           manipulation_high: float,
                           manipulation_low: float,
                           direction: str = 'up') -> Dict[str, float]:
        """
        Standard Deviation da "manipulation leg" (ICT)
        
        Livelli: -1, -2, -2.5, -4 dalla manipulation leg
        """
        move = manipulation_high - manipulation_low
        
        levels = [-1, -2, -2.5, -4]
        targets = {'method': 'ICT StdDev Projection'}
        
        if direction == 'up':
            base = manipulation_high
            for lvl in levels:
                targets[f'level_{abs(lvl)}'] = base + (move * abs(lvl))
        else:
            base = manipulation_low
            for lvl in levels:
                targets[f'level_{abs(lvl)}'] = base - (move * abs(lvl))
        
        return targets
    
    # ========== METODO 6: RANGE/VOLATILITY BASED ==========
    
    def range_based_targets(self,
                           entry_price: float,
                           period: int = 20,
                           direction: str = 'up') -> Dict[str, float]:
        """
        Target basati sul range medio
        """
        if self.df is None:
            raise ValueError("DataFrame non fornito")
        
        # Calcola range giornaliero
        daily_range = self.df['high'] - self.df['low']
        
        adr = daily_range.rolling(window=period).mean().iloc[-1]
        p25 = daily_range.quantile(0.25)
        p50 = daily_range.quantile(0.50)
        p75 = daily_range.quantile(0.75)
        p90 = daily_range.quantile(0.90)
        
        targets = {
            'adr': adr,
            'method': 'Range Based'
        }
        
        mult = 1 if direction == 'up' else -1
        
        targets['conservative'] = entry_price + (p25 * mult)
        targets['medium'] = entry_price + (p50 * mult)
        targets['aggressive'] = entry_price + (p75 * mult)
        targets['extreme'] = entry_price + (p90 * mult)
        targets['full_adr'] = entry_price + (adr * mult)
        
        return targets
    
    # ========== METODO 7: COMPOSITE / CONFLUENZA ==========
    
    def find_confluences(self, 
                        targets: Dict[str, float],
                        tolerance: float = 0.02) -> List[Dict]:
        """
        Trova confluenze tra diversi target
        
        Args:
            targets: Dizionario di target da diversi metodi
            tolerance: Tolleranza percentuale per considerare confluenza
        """
        # Estrai solo i valori numerici
        values = []
        for k, v in targets.items():
            if isinstance(v, (int, float)) and k not in ['method', 'atr_value', 'std_value']:
                values.append((k, v))
        
        if not values:
            return []
        
        # Ordina per valore
        values.sort(key=lambda x: x[1])
        
        # Trova cluster
        clusters = []
        current_cluster = [values[0]]
        
        for name, val in values[1:]:
            if abs(val - current_cluster[-1][1]) / current_cluster[-1][1] <= tolerance:
                current_cluster.append((name, val))
            else:
                if len(current_cluster) >= 2:
                    cluster_vals = [v for _, v in current_cluster]
                    clusters.append({
                        'level': np.mean(cluster_vals),
                        'methods': [n for n, _ in current_cluster],
                        'strength': len(current_cluster),
                        'min': min(cluster_vals),
                        'max': max(cluster_vals)
                    })
                current_cluster = [(name, val)]
        
        # Controlla ultimo cluster
        if len(current_cluster) >= 2:
            cluster_vals = [v for _, v in current_cluster]
            clusters.append({
                'level': np.mean(cluster_vals),
                'methods': [n for n, _ in current_cluster],
                'strength': len(current_cluster),
                'min': min(cluster_vals),
                'max': max(cluster_vals)
            })
        
        return sorted(clusters, key=lambda x: x['strength'], reverse=True)
    
    def composite_analysis(self,
                          entry_price: float,
                          swing_high: float,
                          swing_low: float,
                          retracement_end: float,
                          atr: float = None,
                          direction: str = 'up') -> Dict:
        """
        Analisi composita con tutti i metodi
        
        Returns:
            Dict con tutti i target e le confluenze
        """
        if atr is None and self.df is not None:
            atr = self.calculate_atr()
        
        all_targets = {}
        
        # 1. ATR
        if atr:
            atr_t = self.atr_targets(entry_price, atr, direction=direction)
            all_targets.update({f'atr_{k}': v for k, v in atr_t.items() 
                               if isinstance(v, (int, float))})
        
        # 2. Measured Move
        mm_t = self.measured_move(swing_low, swing_high, retracement_end)
        all_targets.update({f'mm_{k}': v for k, v in mm_t.items() 
                           if isinstance(v, (int, float))})
        
        # 3. Fibonacci
        fib_t = self.fibonacci_extensions(swing_low, swing_high, 
                                         retracement_end, direction)
        all_targets.update({k: v for k, v in fib_t.items() 
                           if k.startswith('fib_')})
        
        # 4. StdDev ICT
        std_t = self.std_channel_targets(swing_high, swing_low, direction)
        all_targets.update({f'std_{k}': v for k, v in std_t.items() 
                           if isinstance(v, (int, float))})
        
        # Trova confluenze
        confluences = self.find_confluences(all_targets)
        
        return {
            'all_targets': all_targets,
            'confluences': confluences,
            'strongest_target': confluences[0] if confluences else None,
            'entry_price': entry_price,
            'direction': direction
        }


# ========== UTILITY FUNCTIONS ==========

def calculate_target_quick(entry: float, 
                          swing_high: float, 
                          swing_low: float,
                          atr: float,
                          direction: str = 'up') -> Dict:
    """
    Calcolo rapido di target senza DataFrame
    
    Esempio:
        targets = calculate_target_quick(
            entry=100,
            swing_high=110,
            swing_low=95,
            atr=3.5,
            direction='up'
        )
    """
    move = swing_high - swing_low
    mult = 1 if direction == 'up' else -1
    
    return {
        # ATR based
        'atr_1x': entry + (atr * mult),
        'atr_2x': entry + (atr * 2 * mult),
        'atr_3x': entry + (atr * 3 * mult),
        
        # Range based
        'range_100': entry + (move * mult),
        'range_150': entry + (move * 1.5 * mult),
        'range_200': entry + (move * 2 * mult),
        
        # Fibonacci (from entry)
        'fib_162': entry + (move * 0.618 * mult),
        'fib_200': entry + (move * 1.0 * mult),
        'fib_262': entry + (move * 1.618 * mult),
    }


def pnf_count_simple(num_columns: int, 
                     box_size: float, 
                     reversal: int,
                     base_price: float,
                     direction: str = 'up') -> float:
    """
    Calcolo P&F semplificato
    
    Esempio:
        target = pnf_count_simple(
            num_columns=12,
            box_size=1.0,
            reversal=3,
            base_price=100,
            direction='up'
        )
        # Result: 100 + (12 * 1.0 * 3) = 136
    """
    cause = num_columns * box_size * reversal
    
    if direction == 'up':
        return base_price + cause
    else:
        return base_price - cause


# ========== ESEMPIO D'USO ==========

if __name__ == "__main__":
    # Esempio senza DataFrame
    print("=" * 60)
    print("ESEMPIO: Calcolo Target Rapido")
    print("=" * 60)
    
    targets = calculate_target_quick(
        entry=100.0,
        swing_high=115.0,
        swing_low=90.0,
        atr=4.5,
        direction='up'
    )
    
    print("\nInput:")
    print("  Entry: $100")
    print("  Swing High: $115")
    print("  Swing Low: $90")
    print("  ATR: $4.5")
    
    print("\nTarget Calcolati:")
    for name, value in sorted(targets.items(), key=lambda x: x[1]):
        print(f"  {name}: ${value:.2f}")
    
    # P&F Count
    print("\n" + "=" * 60)
    print("ESEMPIO: P&F Count Semplice")
    print("=" * 60)
    
    pnf_target = pnf_count_simple(
        num_columns=15,
        box_size=2.0,
        reversal=3,
        base_price=50.0,
        direction='up'
    )
    
    print(f"\nInput:")
    print(f"  Colonne: 15")
    print(f"  Box Size: $2")
    print(f"  Reversal: 3")
    print(f"  Base (minimo): $50")
    print(f"\nFormula: 50 + (15 × 2 × 3) = ${pnf_target:.2f}")
    
    # Fibonacci
    print("\n" + "=" * 60)
    print("ESEMPIO: Fibonacci Extensions")
    print("=" * 60)
    
    calc = PriceTargetCalculator()
    fib = calc.fibonacci_extensions(
        swing_low=100,
        swing_high=150,
        retracement_end=130,
        direction='up'
    )
    
    print("\nInput:")
    print("  Swing Low: $100")
    print("  Swing High: $150")
    print("  Retracement End: $130")
    
    print("\nTarget Fibonacci:")
    for name, value in sorted(fib.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0):
        if name.startswith('fib_'):
            print(f"  {name}: ${value:.2f}")
    
    print("\n" + "=" * 60)
    print("Script pronto per importazione: from price_targets import *")
    print("=" * 60)
