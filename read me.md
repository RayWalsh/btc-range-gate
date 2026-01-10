# BTC Range Gate

A conservative, rules-based regime detector for BTC spot.

## Purpose
Answers one question only:

> "Is BTC currently in a valid sideways range suitable for range trading?"

## Timeframe
- 4H candles
- 7–10 day lookback

## Output
- RANGE VALID
- NO RANGE

## Rules (Locked)
- ≥7 days horizontal containment
- ≥2 upper boundary rejections
- ≥2 lower boundary bounces
- ≥95% closes inside range
- Range width ≥1.5%
- No recent directional expansion

This module does NOT:
- trade
- optimise
- predict
- visualise
