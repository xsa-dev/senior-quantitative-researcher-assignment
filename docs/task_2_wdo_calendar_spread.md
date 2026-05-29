# Task 2 WDO calendar spread

Rows: 1
Contracts: WDOG26 - WDOH26
Source: schema_backed_reconstructed_book
Spread uses only rows with decoded real bid/ask/mid and bid<=ask.

The pipeline emits `outputs/csv/wdo_calendar_spread.csv` and `outputs/plots/wdo_calendar_spread.png`. When the source is `schema_backed_reconstructed_book`, the values come from decoded B3 UMDF/SBE MBO book fields rather than the non-WDO quote CSV.
