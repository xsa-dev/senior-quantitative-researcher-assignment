# Task 2 WDO calendar spread

Rows: 21387
Contracts: WDOG26 - WDOH26
Source: schema_backed_wdo_mbo_timeseries
WDO top-of-book time-series rows: 38772
Near bid/ask/mid first row: 5408.0 / 5420.5 / 5414.25
Far bid/ask/mid first row: 5411.5 / 5482.0 / 5446.75
First spread: -32.5
Spread uses only decoded real bid/ask/mid rows with positive prices and bid<=ask. Contract selection is calendar-sorted by WDO futures month code and aligned with merge_asof tolerance.
When `source=schema_backed_wdo_mbo_timeseries`, Task 2 uses event-driven decoded WDO MBO top-of-book rows rather than a single final reconstructed-book snapshot.

The pipeline emits `outputs/csv/wdo_top_of_book_timeseries.csv`, `outputs/csv/wdo_calendar_spread.csv`, and `outputs/plots/wdo_calendar_spread.png`. When the source is `schema_backed_wdo_mbo_timeseries`, the values come from event-driven decoded B3 UMDF/SBE WDO MBO book fields rather than the non-WDO quote CSV or a single final book snapshot.
