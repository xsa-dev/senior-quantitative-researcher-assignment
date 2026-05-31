#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from quant_assignment.spreads import load_quotes
from quant_assignment.features import compute_features
from quant_assignment.plotting import line_plot

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',default='documents'); ap.add_argument('--output-dir',default='outputs'); ap.add_argument('--symbol',default='WDOG26'); args=ap.parse_args()
    out=Path(args.output_dir); (out/'csv').mkdir(parents=True,exist_ok=True); (out/'plots').mkdir(parents=True,exist_ok=True)
    df=load_quotes(str(Path(args.data_dir)/'quotes_202512260854(in).csv'))
    symbol=args.symbol if args.symbol in set(df.symbol.unique()) else df.symbol.value_counts().index[0]
    requested_note = '' if args.symbol == symbol else f'Requested symbol {args.symbol} was unavailable; selected most liquid available symbol {symbol}.\n'
    f=compute_features(df,symbol)
    f.to_csv(out/'csv/volatility_momentum.csv', index=False)
    if not f.empty:
        line_plot(f,'ts','rv_1min',f'{symbol} realized vol', out/'plots/volatility.png')
        line_plot(f,'ts','mom_z',f'{symbol} momentum z-score', out/'plots/momentum.png')
    momentum_non_na = int(f['mom_z'].notna().sum()) if 'mom_z' in f else 0
    momentum_note = (
        f"Momentum rows with finite z-score: {momentum_non_na}\n"
        "Momentum is computed on irregular quote ticks using an as-of midpoint observed no later than `ts - 30s`; this avoids the all-NaN behavior of exact timestamp-offset `pct_change(freq='30s')`.\n"
    )
    Path('docs/task_3_volatility_momentum.md').write_text(
        f"# Task 3 volatility/momentum\n\n"
        f"Symbol: {symbol}\n"
        f"Rows: {len(f)}\n"
        + requested_note
        + momentum_note
        + "Latency assumption: 400ms decision lag represented by decision_ts column. Rolling statistics are backward-looking, based on data received no later than ts.\n"
    )
if __name__=='__main__': main()
