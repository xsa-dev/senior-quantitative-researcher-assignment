# Task 3 — Volatility and momentum under latency

## Objective
Compute backward-looking volatility and momentum features for a liquid market-data symbol, while explicitly modelling the requested execution/decision latency.

The assignment requested `WDOG26`; that symbol was not available in the quote dataset used for this task, so the pipeline selects the most liquid available symbol instead:

```text
Selected symbol: GOLD-3.26
Rows: 362,448
```

## Outputs
The pipeline emits:

- `outputs/csv/volatility_momentum.csv` — quote-level volatility, momentum and latency-aware decision timestamps.
- `outputs/plots/volatility.png` — realized/EWMA volatility visualization.
- `outputs/plots/momentum.png` — momentum z-score visualization.
- `outputs/reports/summary_metrics.md` — task-level summary metrics.
- `outputs/reports/validation_report.md` — validation and sanity checks.

## Feature construction

### Mid price
All features are based on the quote midpoint:

```text
mid = (bid + ask) / 2
```

Rows with invalid or non-positive prices are excluded upstream by the quote-cleaning pipeline.

### Volatility
The volatility features are backward-looking and use only information observable at or before timestamp `ts`:

- rolling realized volatility over the configured lookback window;
- EWMA volatility for smoother intraday behavior.

Latest validation confirms that volatility features are populated rather than empty:

```text
realized volatility finite rows: 362,216 / 362,448
EWMA volatility finite rows:     362,446 / 362,448
```

### Momentum
Momentum is computed on irregular quote ticks using an as-of lagged midpoint observed no later than:

```text
ts - 30s
```

This is intentionally not implemented with an exact timestamp-offset `pct_change(freq='30s')`, because irregular market ticks rarely land exactly on the requested timestamp. The as-of approach avoids the previous all-NaN failure mode and keeps the feature economically meaningful.

Latest validation:

```text
momentum finite z-score rows: 362,416 / 362,448
```

## Latency model
The strategy assumes a `400ms` decision latency. The output includes a latency-adjusted decision timestamp:

```text
decision_ts = ts + 400ms
```

Latest validation confirms the latency shift is applied consistently:

```text
decision_ts - ts unique milliseconds: [400.0]
```

## Data-integrity notes

- Rolling statistics are backward-looking and do not use future data.
- Momentum uses an as-of historical midpoint, so it is robust to irregular quote spacing.
- The validation report now includes non-empty feature checks for momentum and volatility, preventing silently blank plots from passing unnoticed.
