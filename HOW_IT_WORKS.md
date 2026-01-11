# BTC Regime Engine — How It Works

## Purpose
This system is a conservative, rules-based regime classifier for BTC spot.
It does not trade.
It exists to answer one question daily:

"Is there a structurally valid reason to engage the market?"

## Core Philosophy
- Trade rarely
- Avoid false positives
- Prefer standing down to marginal setups
- Structure > indicators
- Time + price > momentum

## Regimes
The system recognises three regimes:
1. RANGE (mean reversion)
2. TREND (pullback continuation)
3. DRIFT / TRANSITION (no trade)

NO RANGE ≠ MUST TRADE

## Range Logic (Summary)
- 4H candles
- ≥ 7 days containment
- ≥ 2 upper rejections
- ≥ 2 lower bounces
- ≥ 95% closes inside range
- No recent expansion

Purpose: detect boring, defendable ranges.

## Trend Logic (Summary)
- Daily candles
- ~8 day window
- ≥ 4% net move
- Directional persistence
- At least one failed pullback

Purpose: detect early, confirmed trends without breakout chasing.

## Regime Readiness (Non-decisional)
When no strategy is allowed, the system explains:
- What conditions are partially met
- What is still missing
- Why standing down is correct

This layer does NOT enable trades.

## Logging
- One row per day
- Stable schema
- Designed for retrospective review
- Readiness is not logged by default

## Design Constraints
- No ML
- No optimisation
- No execution
- Spot-only
- Human-in-the-loop



Perfect. This is exactly the right moment to lock in the reasoning while it’s still clear in your head.

Below is ready-to-drop text you can put straight into HOW_IT_WORKS.md.
It explains why 8 days and why 4%, in plain, defensible language — not hand-wavy trading lore.

You can treat this as canonical justification for future-you (or anyone else).




🔹 Why an ~8 Day Window for Trend Detection

The trend detection logic evaluates price behaviour over approximately 8 days of daily closes.

This timeframe is intentional.

The purpose of the trend gate is not to react to short-term momentum, news-driven spikes, or isolated impulses. It exists to answer a more structural question:

Has the market genuinely relocated, or is it still oscillating around the same price area?

An 8-day window strikes a deliberate balance:
	•	Too short (e.g. 2–4 days)
BTC can move several percent in a single day and then fully retrace.
Short windows are highly sensitive to:
	•	news events
	•	funding squeezes
	•	thin liquidity periods
These moves often fail to persist.
	•	Too long (e.g. 14–21 days)
Longer windows lag significantly and tend to identify trends only after they are mature.
This encourages late entries and breakout chasing, which this system explicitly avoids.

Using ~8 days forces any potential trend to:
	•	survive multiple market sessions
	•	persist through different liquidity conditions
	•	demonstrate commitment over time, not just speed

In practice, sustained BTC trends tend to either expand meaningfully or fail within about one week.
If price cannot demonstrate directional persistence over this window, it is treated as noise.

The 8-day window therefore acts as a time-based filter, not a trigger.

⸻

🔹 Why a Minimum 4% Net Move Is Required

Directional persistence alone is not sufficient to define a trend.

Price can:
	•	close higher several days in a row
	•	show directional bias
	•	yet still remain effectively in the same location

The trend gate therefore requires a minimum net price displacement of 4% over the evaluation window.

This rule answers a simple but critical question:

Has price actually gone somewhere meaningful?

For BTC:
	•	~1% over a week is common noise
	•	2–3% often reflects probing or grind
	•	4–6% typically indicates real participation and commitment
	•	8%+ suggests a mature move

Requiring a 4% net move ensures that:
	•	the move is large enough to matter
	•	participants have been forced to react
	•	the market has shown intent beyond balance

This prevents the system from classifying:
	•	slow drifts
	•	overlapping candles
	•	grindy consolidations
as trends.

Importantly, the 4% threshold does not trigger a trade on its own.
It only qualifies price action to be considered trend-capable, subject to further structural checks (pullbacks, failures, persistence).



🔹 How Time and Price Work Together

Neither the 8-day window nor the 4% threshold is sufficient on its own.

They work together:
	•	Time ensures the move persists
	•	Price displacement ensures the move matters

Only when price has:
	•	persisted for ~8 days and
	•	relocated by at least 4% and
	•	demonstrated directional structure and failed pullbacks

does the system consider a trend valid.

This design intentionally favors:
	•	early-but-confirmed trends
	•	conservative engagement
	•	fewer, higher-quality opportunities

Standing down during partial moves is not a failure of the system — it is the expected and desired behaviour.

⸻

🧠 Why this matters

Including this justification does three important things:
	1.	Prevents future rule erosion
You (or someone else) won’t casually say “why not 3 days?” or “why not 2%?” without confronting the original intent.
	2.	Keeps the system philosophy intact
These numbers are not optimised parameters — they are filters for structural validity.
	3.	Aligns human intuition with system output
When the engine says “NO TREND”, this document explains why that is correct, not just what happened.

