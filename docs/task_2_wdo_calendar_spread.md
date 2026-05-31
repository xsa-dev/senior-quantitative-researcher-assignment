# Task 2 WDO calendar spread

Rows: 1
Contracts: WDOG26 - WDOH26
Source: schema_backed_reconstructed_book
Near bid/ask/mid: 5404.0 / 5405.5 / 5404.75
Far bid/ask/mid: 5435.5 / 5439.0 / 5437.25
Spread: -32.5
Spread uses only decoded real bid/ask/mid rows with positive prices and bid<=ask. Contract selection is calendar-sorted by WDO futures month code and aligned with merge_asof tolerance.
When only one aligned pair is available, the plot is rendered as an annotated single-observation bar instead of an empty-looking line chart.

The pipeline emits `outputs/csv/wdo_calendar_spread.csv` and `outputs/plots/wdo_calendar_spread.png`. When the source is `schema_backed_reconstructed_book`, the values come from decoded B3 UMDF/SBE MBO book fields rather than the non-WDO quote CSV.
