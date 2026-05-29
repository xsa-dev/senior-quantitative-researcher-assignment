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
        f"# Task 4 gold arbitrage\n\n"
        f"B3: {s1}\n"
        f"MOEX: {s2}\n"
        f"Metrics: {m}\n"
    )
if __name__=='__main__': main()
