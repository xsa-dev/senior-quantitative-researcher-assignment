#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from quant_assignment.spreads import load_quotes, normalize_book_quotes, build_wdo_spread
from quant_assignment.plotting import line_plot
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-dir', default='documents')
    ap.add_argument('--output-dir', default='outputs')
    args = ap.parse_args()
    out = Path(args.output_dir)
    (out / 'csv').mkdir(parents=True, exist_ok=True)
    (out / 'plots').mkdir(parents=True, exist_ok=True)
    Path('docs').mkdir(exist_ok=True)

    quote_path = Path(args.data_dir) / 'quotes_202512260854(in).csv'
    source = 'quotes_csv'
    df = load_quotes(str(quote_path)) if quote_path.exists() else pd.DataFrame()
    s = build_wdo_spread(df) if not df.empty else pd.DataFrame()

    if s.empty:
        book_path = out / 'csv/reconstructed_book.csv'
        book = pd.read_csv(book_path, low_memory=False) if book_path.exists() else pd.DataFrame()
        df = normalize_book_quotes(book)
        s = build_wdo_spread(df)
        source = 'schema_backed_reconstructed_book'

    s.to_csv(out / 'csv/wdo_calendar_spread.csv', index=False)
    if not s.empty:
        line_plot(s, 'ts', 'spread', 'WDO Calendar Spread', out / 'plots/wdo_calendar_spread.png')
        note = (
            f"Rows: {len(s)}\n"
            f"Contracts: {s['near_contract'].iloc[0]} - {s['far_contract'].iloc[0]}\n"
            f"Source: {source}\n"
            f"Near bid/ask/mid: {s['near_bid'].iloc[0]} / {s['near_ask'].iloc[0]} / {s['near_mid'].iloc[0]}\n"
            f"Far bid/ask/mid: {s['far_bid'].iloc[0]} / {s['far_ask'].iloc[0]} / {s['far_mid'].iloc[0]}\n"
            f"Spread: {s['spread'].iloc[0]}\n"
            "Spread uses only decoded real bid/ask/mid rows with positive prices and bid<=ask. Contract selection is calendar-sorted by WDO futures month code and aligned with merge_asof tolerance.\n"
        )
    else:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.axis('off')
        ax.text(0.02, 0.65, 'WDO calendar spread unavailable', fontsize=16, weight='bold')
        ax.text(0.02, 0.45, 'No pair of valid WDO futures top-of-book rows was available after schema-backed decode.', fontsize=10)
        ax.text(0.02, 0.30, 'The CSV output is intentionally empty rather than fabricated.', fontsize=10)
        fig.tight_layout(); fig.savefig(out / 'plots/wdo_calendar_spread.png'); plt.close(fig)
        symbols = ', '.join(sorted(map(str, df['symbol'].dropna().unique()))[:20]) if 'symbol' in df.columns else ''
        note = f"Rows: 0\nAvailable quote symbols: {symbols}\nReason: no valid WDO futures pair available after honest decode.\n"
    Path('docs/task_2_wdo_calendar_spread.md').write_text(
        "# Task 2 WDO calendar spread\n\n"
        + note
        + "\nThe pipeline emits `outputs/csv/wdo_calendar_spread.csv` and `outputs/plots/wdo_calendar_spread.png`. When the source is `schema_backed_reconstructed_book`, the values come from decoded B3 UMDF/SBE MBO book fields rather than the non-WDO quote CSV.\n"
    )


if __name__ == '__main__':
    main()
