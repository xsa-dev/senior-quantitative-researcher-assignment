# Task 2 — WDO calendar spread

## Objective
Build a WDO calendar-spread time series from decoded B3 order-book data, using real bid/ask/mid prices only. The spread is defined as:

```text
near_contract_mid - far_contract_mid
```

For the latest run, the selected contracts are:

```text
WDOG26 - WDOH26
```

## Data source
Task 2 now uses the schema-backed decoded WDO MBO replay:

```text
source = schema_backed_wdo_mbo_timeseries
```

This means the spread is generated from event-driven decoded B3 UMDF/SBE WDO order-book updates, not from the non-WDO quote CSV and not from a single final reconstructed-book snapshot.

## Outputs
The pipeline emits:

- `outputs/csv/wdo_top_of_book_timeseries.csv` — event-driven WDO top-of-book time series.
- `outputs/csv/wdo_calendar_spread.csv` — aligned calendar-spread observations.
- `outputs/plots/wdo_calendar_spread.png` — spread visualization.

## Latest run summary

```text
WDO top-of-book rows: 38,772
Calendar-spread rows: 21,387
Contracts: WDOG26 - WDOH26
First near bid / ask / mid: 5408.0 / 5420.5 / 5414.25
First far bid / ask / mid: 5411.5 / 5482.0 / 5446.75
First spread: -32.5
```

## Method

1. Decode WDO futures instruments from B3 `SecurityDefinition` messages.
2. Replay schema-backed WDO MBO order events into top-of-book states.
3. Keep only valid top-of-book rows:
   - positive bid/ask prices;
   - `bid <= ask`;
   - finite midpoint.
4. Sort contracts by WDO futures month code.
5. Select the near/far calendar pair.
6. Align near and far midpoint series with `merge_asof` tolerance.
7. Compute the spread as `near_mid - far_mid`.

## Data-integrity notes

- Market fields are not fabricated: symbol, side, price, size and order identifiers come from schema-backed B3 message decoding.
- Crossed or invalid top-of-book states are excluded before spread construction.
- The time series contains real aligned observations, so the chart is no longer a single-point or visually empty plot.
