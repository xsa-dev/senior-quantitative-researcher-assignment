#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from quant_assignment.spreads import load_quotes
from quant_assignment.arbitrage import prepare_gold_pairs, metrics
from quant_assignment.plotting import line_plot

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',default='documents'); ap.add_argument('--output-dir',default='outputs'); args=ap.parse_args()
    out=Path(args.output_dir); (out/'csv').mkdir(parents=True,exist_ok=True); (out/'plots').mkdir(parents=True,exist_ok=True)
    df=load_quotes(str(Path(args.data_dir)/'quotes_202512260854(in).csv'))
    g,s1,s2=prepare_gold_pairs(df)
    g.to_csv(out/'csv/gold_arbitrage_signals.csv', index=False)
    if not g.empty:
        line_plot(g,'ts','raw_spread',f'{s1} vs {s2} spread', out/'plots/gold_spread.png')
        line_plot(g,'ts','zscore',f'{s1} vs {s2} zscore', out/'plots/gold_spread_zscore.png')
        line_plot(g,'ts','cum_pnl',f'{s1} vs {s2} strategy cum pnl', out/'plots/gold_arbitrage_signals.png')
    m=metrics(g)
    Path('docs/task_4_gold_arbitrage.md').write_text(
        f"# Task 4 — B3 vs MOEX gold arbitrage\n\n"
        f"## Objective\n"
        f"Build a research prototype for a cross-market gold-futures relative-value signal between B3 and MOEX, using aligned quote midpoints and shifted rolling statistics to avoid look-ahead bias.\n\n"
        f"## Selected instruments\n\n"
        f"```text\n"
        f"B3 symbol:  {s1}\n"
        f"MOEX symbol: {s2}\n"
        f"```\n\n"
        f"The selected contracts are the most liquid available B3 `GLD*` and MOEX `GOLD*` symbols in the supplied quotes dataset.\n\n"
        f"## Outputs\n\n"
        f"The pipeline emits:\n\n"
        f"- `outputs/csv/gold_arbitrage_signals.csv` — aligned spread, z-score, position and PnL research table.\n"
        f"- `outputs/plots/gold_spread.png` — raw B3 minus MOEX midpoint spread.\n"
        f"- `outputs/plots/gold_spread_zscore.png` — shifted rolling z-score used for signals.\n"
        f"- `outputs/plots/gold_arbitrage_signals.png` — cumulative prototype PnL.\n\n"
        f"## Method\n\n"
        f"1. Compute midpoints as `(bid + ask) / 2` for all valid quotes.\n"
        f"2. Select the most liquid B3 gold future and MOEX gold future.\n"
        f"3. Align both markets with `merge_asof(..., direction='nearest', tolerance='2s')`.\n"
        f"4. Compute `raw_spread = b3_mid - moex_mid`.\n"
        f"5. Estimate rolling spread mean and standard deviation over 300 observations, shifted by one row before signal calculation.\n"
        f"6. Trade a mean-reversion prototype using z-score thresholds:\n"
        f"   - enter short spread when `zscore > 2`;\n"
        f"   - enter long spread when `zscore < -2`;\n"
        f"   - exit when `abs(zscore) < 0.5`;\n"
        f"   - stop adverse extensions beyond `abs(zscore) > 3`.\n"
        f"7. Apply a simple transaction-cost proxy of `0.05` per position change.\n\n"
        f"## Latest run summary\n\n"
        f"```text\n"
        f"Aligned rows:  {len(g):,}\n"
        f"Total return:  {m.get('total_return', float('nan')):.6f}\n"
        f"Trades:        {m.get('num_trades', 0):,}\n"
        f"Hit rate:      {m.get('hit_rate', float('nan')):.6f}\n"
        f"Max drawdown:  {m.get('max_drawdown', float('nan')):.6f}\n"
        f"```\n\n"
        f"## Data-integrity notes\n\n"
        f"- The z-score normalization uses only prior observations because `spread_mean` and `spread_std` are shifted by one row.\n"
        f"- The reported PnL is a research diagnostic, not a production backtest: it does not model exchange fees, margin, FX conversion, queue priority or execution slippage beyond the simple transaction-cost proxy.\n"
        f"- The output should be interpreted as evidence of signal construction and validation discipline rather than as a deployable trading strategy.\n"
    )
if __name__=='__main__': main()
