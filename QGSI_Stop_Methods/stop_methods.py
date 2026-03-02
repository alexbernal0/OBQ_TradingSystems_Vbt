"""
stop_methods.py — QGSI Stop Method Library
===========================================
12 stop types as pure numpy functions. No backtrader, no class dependencies.
Source: Stop Methods (1).ipynb — rewritten for vectorized research pipeline.

Uniform signature
-----------------
    stop_fn(entry, highs, lows, closes, atrs, is_long, **params) -> np.ndarray

    entry   : float   — entry price (signal bar close)
    highs   : (K,)    — forward bar highs   (bars entry+1 … entry+K)
    lows    : (K,)    — forward bar lows
    closes  : (K,)    — forward bar closes
    atrs    : (K,)    — pre-computed ATR at each forward bar (EWM span)
    is_long : bool    — True = Long, False = Short

    Returns : (K,) float array — stop price active at each forward bar.
              Stop is "hit" on bar k when:
                Long:  lows[k]  <= stop[k]
                Short: highs[k] >= stop[k]

    Exception: trailing_atr_with_target() returns (stops, target_price).

Stop types
----------
    1.  fixed_pct             — entry ± (pct × entry). Never moves.
    2.  fixed_atr             — entry ± (mult × ATR_entry). Never moves.
    3.  trailing_pct          — stop trails at pct% from running extreme.
    4.  trailing_atr          — chandelier: extreme ± (mult × ATR). Ratchets only.
    5.  parabolic_sar         — SAR with AF acceleration. Tightens as trade extends.
    6.  breakeven_pct         — hard % stop → moves to entry after trigger %.
    7.  breakeven_atr         — hard ATR stop → moves to entry after ATR trigger.
    8.  quantile_stop         — stop distance from historical return distribution.
    9.  swing_hl_stop         — stop beyond most recent swing low/high.
    10. atr_pct_hybrid        — entry ± (pct×entry + mult×ATR). Adaptive buffer.
    11. tgt_then_trail        — hard ATR stop → trailing ATR stop after target hit.
    12. trailing_atr_with_target — ATR trailing stop + fixed ATR profit target.

Registry
--------
    STOP_REGISTRY : dict[str, callable]  — all functions by name
"""

from __future__ import annotations

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# 1. Fixed Percentage Stop
# ─────────────────────────────────────────────────────────────────────────────

def fixed_pct(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    pct: float = 0.50,
) -> np.ndarray:
    """
    Fixed percentage stop. Set once at entry, never moves.

    params:
        pct : stop distance as % of entry price (default 0.50 = 0.50%)
    """
    K = len(highs)
    level = entry * (1.0 - pct / 100.0) if is_long else entry * (1.0 + pct / 100.0)
    return np.full(K, level, dtype=float)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Fixed ATR Stop
# ─────────────────────────────────────────────────────────────────────────────

def fixed_atr(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    mult: float = 2.0,
) -> np.ndarray:
    """
    Fixed ATR stop. Uses ATR value at entry bar, never updates.

    params:
        mult : ATR multiplier (default 2.0)
    """
    K    = len(highs)
    atr0 = float(np.asarray(atrs)[0])
    level = entry - mult * atr0 if is_long else entry + mult * atr0
    return np.full(K, level, dtype=float)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Trailing Percentage Stop
# ─────────────────────────────────────────────────────────────────────────────

def trailing_pct(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    pct: float = 0.50,
) -> np.ndarray:
    """
    Trailing percentage stop. Stop trails pct% below the running max high (Long)
    or above the running min low (Short). Only moves in favor — never against.

    params:
        pct : trailing distance as % of the running extreme (default 0.50%)
    """
    highs = np.asarray(highs, dtype=float)
    lows  = np.asarray(lows,  dtype=float)
    K     = len(highs)
    stops = np.empty(K, dtype=float)

    if is_long:
        extreme = entry
        for k in range(K):
            if highs[k] > extreme:
                extreme = highs[k]
            stops[k] = extreme * (1.0 - pct / 100.0)
    else:
        extreme = entry
        for k in range(K):
            if lows[k] < extreme:
                extreme = lows[k]
            stops[k] = extreme * (1.0 + pct / 100.0)

    return stops


# ─────────────────────────────────────────────────────────────────────────────
# 4. Trailing ATR Stop (Chandelier)
# ─────────────────────────────────────────────────────────────────────────────

def trailing_atr(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    mult: float = 3.0,
) -> np.ndarray:
    """
    Chandelier ATR trailing stop.
      Long:  stop = running_max_high − mult × ATR   (ratchets up only)
      Short: stop = running_min_low  + mult × ATR   (ratchets down only)

    ATR updates each bar. Stop level never moves against the position.

    params:
        mult : ATR multiplier (default 3.0)
    """
    highs = np.asarray(highs, dtype=float)
    lows  = np.asarray(lows,  dtype=float)
    atrs  = np.asarray(atrs,  dtype=float)
    K     = len(highs)
    stops = np.empty(K, dtype=float)

    if is_long:
        extreme = entry
        stop    = entry - mult * atrs[0]
        for k in range(K):
            if highs[k] > extreme:
                extreme = highs[k]
            candidate = extreme - mult * atrs[k]
            stop = max(stop, candidate)   # only ratchet up
            stops[k] = stop
    else:
        extreme = entry
        stop    = entry + mult * atrs[0]
        for k in range(K):
            if lows[k] < extreme:
                extreme = lows[k]
            candidate = extreme + mult * atrs[k]
            stop = min(stop, candidate)   # only ratchet down
            stops[k] = stop

    return stops


# ─────────────────────────────────────────────────────────────────────────────
# 5. Parabolic SAR Stop
# ─────────────────────────────────────────────────────────────────────────────

def parabolic_sar(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    af_start: float = 0.02,
    af_step:  float = 0.02,
    af_max:   float = 0.20,
) -> np.ndarray:
    """
    Parabolic SAR stop. SAR tightens as the trade extends in favor.
    Used as a one-direction stop only (no reversal during the trade).

    params:
        af_start : initial acceleration factor (default 0.02)
        af_step  : AF increment on each new extreme (default 0.02)
        af_max   : maximum AF cap (default 0.20)
    """
    highs = np.asarray(highs, dtype=float)
    lows  = np.asarray(lows,  dtype=float)
    K     = len(highs)
    stops = np.empty(K, dtype=float)

    af  = af_start
    ep  = entry
    # Initialize SAR slightly behind entry
    sar = entry * (1.0 - 0.002) if is_long else entry * (1.0 + 0.002)

    for k in range(K):
        if is_long:
            if highs[k] > ep:
                ep = highs[k]
                af = min(af + af_step, af_max)
            sar = sar + af * (ep - sar)
            # SAR cannot be above the prior two lows
            if k >= 1:
                sar = min(sar, lows[k - 1])
            if k >= 2:
                sar = min(sar, lows[k - 2])
        else:
            if lows[k] < ep:
                ep = lows[k]
                af = min(af + af_step, af_max)
            sar = sar - af * (sar - ep)
            # SAR cannot be below the prior two highs
            if k >= 1:
                sar = max(sar, highs[k - 1])
            if k >= 2:
                sar = max(sar, highs[k - 2])

        stops[k] = sar

    return stops


# ─────────────────────────────────────────────────────────────────────────────
# 6. Break-Even Percentage Stop
# ─────────────────────────────────────────────────────────────────────────────

def breakeven_pct(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    initial_pct: float = 0.50,
    trigger_pct: float = 0.50,
) -> np.ndarray:
    """
    Two-phase percentage stop:
      Phase 1: hard stop at entry ± initial_pct%
      Phase 2: once price moves trigger_pct% in favor → stop slides to entry (breakeven)

    params:
        initial_pct : initial stop distance as % of entry (default 0.50%)
        trigger_pct : favorable move % to activate breakeven (default = initial_pct)
    """
    highs = np.asarray(highs, dtype=float)
    lows  = np.asarray(lows,  dtype=float)
    K     = len(highs)
    stops = np.empty(K, dtype=float)

    initial_stop  = entry * (1.0 - initial_pct / 100.0) if is_long else entry * (1.0 + initial_pct / 100.0)
    trigger_level = entry * (1.0 + trigger_pct / 100.0) if is_long else entry * (1.0 - trigger_pct / 100.0)
    be_active = False

    for k in range(K):
        if not be_active:
            if is_long and highs[k] >= trigger_level:
                be_active = True
            elif not is_long and lows[k] <= trigger_level:
                be_active = True
        stops[k] = entry if be_active else initial_stop

    return stops


# ─────────────────────────────────────────────────────────────────────────────
# 7. Break-Even ATR Stop
# ─────────────────────────────────────────────────────────────────────────────

def breakeven_atr(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    stop_mult:    float = 2.0,
    trigger_mult: float = 2.0,
) -> np.ndarray:
    """
    Two-phase ATR stop:
      Phase 1: hard stop at entry ± (stop_mult × ATR_entry)
      Phase 2: once price moves trigger_mult × ATR_entry in favor → stop = entry

    params:
        stop_mult    : initial stop in ATR units (default 2.0)
        trigger_mult : favorable ATR move to activate breakeven (default = stop_mult)
    """
    highs = np.asarray(highs, dtype=float)
    lows  = np.asarray(lows,  dtype=float)
    atrs  = np.asarray(atrs,  dtype=float)
    K     = len(highs)
    stops = np.empty(K, dtype=float)

    atr0          = atrs[0]
    initial_stop  = entry - stop_mult * atr0 if is_long else entry + stop_mult * atr0
    trigger_level = entry + trigger_mult * atr0 if is_long else entry - trigger_mult * atr0
    be_active     = False

    for k in range(K):
        if not be_active:
            if is_long and highs[k] >= trigger_level:
                be_active = True
            elif not is_long and lows[k] <= trigger_level:
                be_active = True
        stops[k] = entry if be_active else initial_stop

    return stops


# ─────────────────────────────────────────────────────────────────────────────
# 8. Historical Quantile Stop
# ─────────────────────────────────────────────────────────────────────────────

def quantile_stop(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    hist_returns: np.ndarray | None = None,
    quantile: float = 0.05,
    fallback_pct: float = 1.0,
) -> np.ndarray:
    """
    Volatility-calibrated stop from the historical return distribution.
    Stop distance = |quantile(hist_returns, q)| × entry.
    Adapts automatically to each symbol's realized volatility regime.

    params:
        hist_returns : pre-entry returns array (e.g. 252 bars of % returns).
                       If None or too short, falls back to fixed fallback_pct%.
        quantile     : tail probability — 0.05 = 5th percentile (default)
        fallback_pct : fallback fixed % if hist_returns unavailable (default 1.0%)
    """
    K = len(highs)

    if hist_returns is None or len(hist_returns) < 20:
        level = entry * (1.0 - fallback_pct / 100.0) if is_long else entry * (1.0 + fallback_pct / 100.0)
    else:
        q = float(quantile) if is_long else float(1.0 - quantile)
        q_ret   = float(np.quantile(hist_returns, q))   # negative for downside
        dist    = abs(q_ret) * entry
        level   = entry - dist if is_long else entry + dist

    return np.full(K, level, dtype=float)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Swing High / Low Stop
# ─────────────────────────────────────────────────────────────────────────────

def swing_hl_stop(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    pre_entry_lows:  np.ndarray | None = None,
    pre_entry_highs: np.ndarray | None = None,
    lookback:    int   = 5,
    buffer_pct:  float = 0.10,
    fallback_pct: float = 0.50,
) -> np.ndarray:
    """
    Stop placed just beyond the most recent swing low (Long) or swing high (Short)
    prior to entry. Uses a small buffer to avoid noise wicks.
    Fixed for the life of the trade.

    params:
        pre_entry_lows  : recent lows before entry bar (required for Long)
        pre_entry_highs : recent highs before entry bar (required for Short)
        lookback        : order for local extrema detection (default 5 bars)
        buffer_pct      : % buffer beyond the swing level (default 0.10%)
        fallback_pct    : fixed % fallback if swing data unavailable (default 0.50%)
    """
    K = len(highs)

    try:
        from scipy.signal import argrelextrema

        if is_long:
            if pre_entry_lows is None or len(pre_entry_lows) < lookback * 2 + 1:
                raise ValueError('insufficient pre-entry lows')
            arr = np.asarray(pre_entry_lows[-lookback * 2:], dtype=float)
            idx = argrelextrema(arr, np.less, order=lookback)[0]
            if len(idx) == 0:
                swing = float(np.min(arr))
            else:
                swing = float(arr[idx[-1]])
            level = swing * (1.0 - buffer_pct / 100.0)
        else:
            if pre_entry_highs is None or len(pre_entry_highs) < lookback * 2 + 1:
                raise ValueError('insufficient pre-entry highs')
            arr = np.asarray(pre_entry_highs[-lookback * 2:], dtype=float)
            idx = argrelextrema(arr, np.greater, order=lookback)[0]
            if len(idx) == 0:
                swing = float(np.max(arr))
            else:
                swing = float(arr[idx[-1]])
            level = swing * (1.0 + buffer_pct / 100.0)

    except Exception:
        # Fallback: fixed % stop
        level = entry * (1.0 - fallback_pct / 100.0) if is_long else entry * (1.0 + fallback_pct / 100.0)

    return np.full(K, level, dtype=float)


# ─────────────────────────────────────────────────────────────────────────────
# 10. ATR + Percentage Hybrid Stop
# ─────────────────────────────────────────────────────────────────────────────

def atr_pct_hybrid(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    pct:  float = 0.25,
    mult: float = 1.0,
) -> np.ndarray:
    """
    Adaptive stop combining a fixed % floor and an ATR buffer:
        stop_distance = (pct/100 × entry) + (mult × ATR_entry)

    Wider than pure % in high-vol regimes; tighter than pure ATR in low-vol.
    Fixed at entry — does not trail.

    params:
        pct  : % component of stop distance (default 0.25%)
        mult : ATR multiplier component (default 1.0)
    """
    K    = len(highs)
    atr0 = float(np.asarray(atrs)[0])
    dist = entry * pct / 100.0 + mult * atr0
    level = entry - dist if is_long else entry + dist
    return np.full(K, level, dtype=float)


# ─────────────────────────────────────────────────────────────────────────────
# 11. Target-Then-Trail Stop
# ─────────────────────────────────────────────────────────────────────────────

def tgt_then_trail(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    hard_mult:   float = 2.0,
    trail_mult:  float = 2.0,
    target_mult: float = 2.0,
) -> np.ndarray:
    """
    Two-phase stop strategy:
      Phase 1: hard fixed ATR stop at entry ± (hard_mult × ATR_entry)
      Phase 2: once price reaches entry ± (target_mult × ATR_entry),
               switch to ATR chandelier trailing stop (trail_mult × ATR)

    Protects capital with a hard stop early; locks in gains with a trail after target.

    params:
        hard_mult   : initial hard stop in ATR units (default 2.0)
        trail_mult  : trailing stop in ATR units after activation (default 2.0)
        target_mult : favorable ATR move required to activate trailing (default 2.0)
    """
    highs = np.asarray(highs, dtype=float)
    lows  = np.asarray(lows,  dtype=float)
    atrs  = np.asarray(atrs,  dtype=float)
    K     = len(highs)
    stops = np.empty(K, dtype=float)

    atr0              = atrs[0]
    hard_stop         = entry - hard_mult * atr0 if is_long else entry + hard_mult * atr0
    target_px         = entry + target_mult * atr0 if is_long else entry - target_mult * atr0
    trailing_active   = False
    extreme           = entry

    for k in range(K):
        if not trailing_active:
            if is_long and highs[k] >= target_px:
                trailing_active = True
                extreme = highs[k]
            elif not is_long and lows[k] <= target_px:
                trailing_active = True
                extreme = lows[k]

        if trailing_active:
            if is_long:
                if highs[k] > extreme:
                    extreme = highs[k]
                trail   = extreme - trail_mult * atrs[k]
                stops[k] = max(trail, hard_stop)
            else:
                if lows[k] < extreme:
                    extreme = lows[k]
                trail   = extreme + trail_mult * atrs[k]
                stops[k] = min(trail, hard_stop)
        else:
            stops[k] = hard_stop

    return stops


# ─────────────────────────────────────────────────────────────────────────────
# 12. ATR Trailing Stop with Fixed Target
# ─────────────────────────────────────────────────────────────────────────────

def trailing_atr_with_target(
    entry: float, highs, lows, closes, atrs, is_long: bool,
    stop_mult:   float = 2.0,
    target_mult: float = 4.0,
) -> tuple[np.ndarray, float]:
    """
    ATR trailing stop paired with a fixed ATR profit target.

    Returns BOTH the stop level array AND the fixed target price so the caller
    can apply "stop hit" OR "target hit" exit logic with priority rules.

    Exit priority: target hit on same bar as stop → caller decides (convention: TARGET wins).

    params:
        stop_mult   : ATR multiplier for the trailing stop (default 2.0)
        target_mult : ATR multiplier for the profit target from entry (default 4.0)

    Returns:
        stops  : (K,) array — trailing stop level at each bar
        target : float — fixed profit target price
    """
    highs = np.asarray(highs, dtype=float)
    lows  = np.asarray(lows,  dtype=float)
    atrs  = np.asarray(atrs,  dtype=float)
    K     = len(highs)
    stops = np.empty(K, dtype=float)

    atr0    = atrs[0]
    target  = entry + target_mult * atr0 if is_long else entry - target_mult * atr0
    extreme = entry
    stop    = entry - stop_mult * atr0 if is_long else entry + stop_mult * atr0

    for k in range(K):
        if is_long:
            if highs[k] > extreme:
                extreme = highs[k]
            candidate = extreme - stop_mult * atrs[k]
            stop = max(stop, candidate)
        else:
            if lows[k] < extreme:
                extreme = lows[k]
            candidate = extreme + stop_mult * atrs[k]
            stop = min(stop, candidate)
        stops[k] = stop

    return stops, target


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────

STOP_REGISTRY: dict[str, callable] = {
    'fixed_pct':               fixed_pct,
    'fixed_atr':               fixed_atr,
    'trailing_pct':            trailing_pct,
    'trailing_atr':            trailing_atr,
    'parabolic_sar':           parabolic_sar,
    'breakeven_pct':           breakeven_pct,
    'breakeven_atr':           breakeven_atr,
    'quantile':                quantile_stop,
    'swing_hl':                swing_hl_stop,
    'atr_pct_hybrid':          atr_pct_hybrid,
    'tgt_then_trail':          tgt_then_trail,
    'trailing_atr_w_target':   trailing_atr_with_target,
}
