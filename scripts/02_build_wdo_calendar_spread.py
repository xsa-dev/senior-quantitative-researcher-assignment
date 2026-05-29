#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from quant_assignment.spreads import load_quotes, build_wdo_spread
from quant_assignment.plotting import line_plot
import matplotlib.pyplot as plt

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',default='documents'); ap.add_argument('--output-dir',default='outputs'); args=ap.parse_args()
    out=Path(args.output_dir); (out/'csv').mkdir(parents=True,exist_ok=True); (out/'plots').mkdir(parents=True,exist_ok=True); Path('docs').mkdir(exist_ok=True)
    df=load_quotes(str(Path(args.data_dir)/'quotes_202512260854(in).csv'))
    s=build_wdo_spread(df)
    s.to_csv(out/'csv/wdo_calendar_spread.csv', index=False)
    if not s.empty:
        line_plot(s,'ts','spread','WDO Calendar Spread', out/'plots/wdo_calendar_spread.png')
        note=f"Rows: {len(s)}\nContracts: {s['near_contract'].iloc[0]} - {s['far_contract'].iloc[0]}\n"
    else:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.axis('off')
        ax.text(0.02, 0.65, 'WDO calendar spread unavailable', fontsize=16, weight='bold')
        ax.text(0.02, 0.45, 'No WDO symbols were found in the provided quotes CSV, and PCAP prices cannot be decoded without B3 schema.', fontsize=10)
        ax.text(0.02, 0.30, 'The CSV output is intentionally empty rather than fabricated.', fontsize=10)
        fig.tight_layout(); fig.savefig(out/'plots/wdo_calendar_spread.png'); plt.close(fig)
        symbols=', '.join(sorted(map(str, df['symbol'].dropna().unique()))[:20])
        note=f"Rows: 0\nAvailable quote symbols: {symbols}\nReason: no WDO futures prices available after honest decode.\n"
    Path('docs/task_2_wdo_calendar_spread.md').write_text(
        "# Task 2 WDO calendar spread\n\n"
        + note
        + "\nThe pipeline still emits `outputs/csv/wdo_calendar_spread.csv` and `outputs/plots/wdo_calendar_spread.png` so the assignment mapping is reproducible. The plot is a diagnostic availability plot when the spread cannot be computed.\n"
    )
if __name__=='__main__': main()
