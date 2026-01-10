# config.py
# LOCKED TRADING RULES — DO NOT MODIFY WITHOUT EXPLICIT REVIEW

SYMBOL = "BTCUSDT"
INTERVAL = "4h"

LOOKBACK_DAYS_MIN = 7
LOOKBACK_DAYS_MAX = 10

MIN_RANGE_WIDTH_PCT = 1.5
MIN_CLOSES_INSIDE_PCT = 95.0
MIN_REJECTIONS = 2
MIN_BOUNCES = 2

# Conservative tolerances (explicit + reviewable)
PROXIMITY_PCT = 0.25          # % distance considered "near" boundary
TREND_EXPANSION_PCT = 1.00    # % net move allowed over recent window

CANDLES_PER_DAY = 6