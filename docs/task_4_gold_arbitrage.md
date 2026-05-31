# Task 4 — B3 vs MOEX gold arbitrage

## Objective
Build a research prototype for a cross-market gold-futures relative-value signal between B3 and MOEX, using aligned quote midpoints and shifted rolling statistics to avoid look-ahead bias.

## Selected instruments

```text
B3 symbol:  GLDG26
MOEX symbol: GOLD-3.26
```

The selected contracts are the most liquid available B3 `GLD*` and MOEX `GOLD*` symbols in the supplied quotes dataset.

## Outputs

The pipeline emits:

- `outputs/csv/gold_arbitrage_signals.csv` — aligned spread, z-score, position and PnL research table.
- `outputs/plots/gold_spread.png` — raw B3 minus MOEX midpoint spread.
- `outputs/plots/gold_spread_zscore.png` — shifted rolling z-score used for signals.
- `outputs/plots/gold_arbitrage_signals.png` — cumulative prototype PnL.

## Method

1. Compute midpoints as `(bid + ask) / 2` for all valid quotes.
2. Select the most liquid B3 gold future and MOEX gold future.
3. Align both markets with `merge_asof(..., direction='nearest', tolerance='2s')`.
4. Compute `raw_spread = b3_mid - moex_mid`.
5. Estimate rolling spread mean and standard deviation over 300 observations, shifted by one row before signal calculation.
6. Trade a mean-reversion prototype using z-score thresholds:
   - enter short spread when `zscore > 2`;
   - enter long spread when `zscore < -2`;
   - exit when `abs(zscore) < 0.5`;
   - stop adverse extensions beyond `abs(zscore) > 3`.
7. Apply a simple transaction-cost proxy of `0.05` per position change.

## Latest run summary

```text
Aligned rows:  120,538
Total return:  798.325000
Trades:        4,893
Hit rate:      0.108182
Max drawdown:  -53.500000
```

## Data-integrity notes

- The z-score normalization uses only prior observations because `spread_mean` and `spread_std` are shifted by one row.
- The reported PnL is a research diagnostic, not a production backtest: it does not model exchange fees, margin, FX conversion, queue priority or execution slippage beyond the simple transaction-cost proxy.
- The output should be interpreted as evidence of signal construction and validation discipline rather than as a deployable trading strategy.
