# trade_plan.py
"""
Trade Plan Generator + Logger

Purpose:
- Generate numeric, text-only trade plans
- Expose structured metadata for journaling
- No execution, no signals
"""

from typing import Dict, List
from datetime import datetime, timezone
import csv
import os

from range_gate import RangeDecision
from trend_gate import TrendDecision

TRADE_LOG_FILE = "trade_plan_log.csv"


# -----------------------------
# RANGE TRADE PLAN
# -----------------------------

def generate_range_trade_plan(range_decision: RangeDecision) -> Dict:
    L = range_decision.lower
    U = range_decision.upper
    W = U - L

    plan = {
        "strategy": "RANGE TRADING",
        "regime": "RANGE",
        "range_lower": L,
        "range_upper": U,
        "entry_zone_low": L,
        "entry_zone_high": L + 0.15 * W,
        "invalidation": L - 0.10 * W,
        "tp1": L + 0.50 * W,
        "tp2": U - 0.10 * W,
        "notes": "Mean reversion inside validated range",
    }

    return plan


# -----------------------------
# TREND TRADE PLAN
# -----------------------------

def generate_trend_trade_plan(trend_decision: TrendDecision) -> Dict:
    O = trend_decision.trend_origin
    H = trend_decision.trend_high
    R = H - O

    plan = {
        "strategy": "TREND PULLBACK",
        "regime": "TREND_UP",
        "trend_origin": O,
        "trend_high": H,
        "pullback_zone_high": H - 0.30 * R,
        "pullback_zone_low": H - 0.50 * R,
        "invalidation": O,
        "target": H,
        "notes": "Pullback continuation in confirmed trend",
    }

    return plan


# -----------------------------
# LOGGING
# -----------------------------

def log_trade_plan(plan: Dict, spot_price: float):
    file_exists = os.path.isfile(TRADE_LOG_FILE)

    with open(TRADE_LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp_utc",
                "regime",
                "strategy",
                "spot_price",
                "range_lower",
                "range_upper",
                "entry_zone_low",
                "entry_zone_high",
                "pullback_zone_low",
                "pullback_zone_high",
                "invalidation",
                "tp1",
                "tp2",
                "target",
                "notes",
            ])

        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            plan.get("regime"),
            plan.get("strategy"),
            f"{spot_price:.2f}",
            plan.get("range_lower"),
            plan.get("range_upper"),
            plan.get("entry_zone_low"),
            plan.get("entry_zone_high"),
            plan.get("pullback_zone_low"),
            plan.get("pullback_zone_high"),
            plan.get("invalidation"),
            plan.get("tp1"),
            plan.get("tp2"),
            plan.get("target"),
            plan.get("notes"),
        ])