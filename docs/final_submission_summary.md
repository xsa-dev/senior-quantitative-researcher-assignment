# Final submission summary

## Executive summary
This repository is ready as a defensible, reproducible GitHub solution for the senior quantitative researcher assignment. The full local pipeline runs with `make all`, tests pass cleanly, large raw/generated artifacts stay out of Git, and B3 PCAP economic fields are populated from schema-backed UMDF/SBE decoding rather than fabricated heuristics.

The assignment-critical B3 path is resolved: instrument definitions, WDO futures symbols, MBO order events, reconstructed top-of-book rows, and a full intraday WDO calendar-spread time series are produced from decoded B3 Binary UMDF/SBE frames. The solution is intentionally audit-friendly: unsupported templates remain diagnostic evidence, every market field has provenance, and validation checks catch empty feature/plot regressions such as all-NaN momentum.

## Run commands

```bash
cd senior-quantitative-researcher-assignment
make install
make all
```

Individual targets:

```bash
make discover
make parse-pcap
make spread
make features
make arbitrage
make validate
make test
```

## Verified quality gates
Latest local verification:

- `make all`: completes successfully.
- `make test`: passes cleanly (`14 passed`).
- Required output CSVs exist.
- Validation report is regenerated at `outputs/reports/validation_report.md`.
- Economic B3 fields pass only with schema provenance.
- WDO spread source is `schema_backed_wdo_mbo_timeseries`.
- Heavy `documents/` and generated `outputs/` artifacts remain ignored by Git except `.gitkeep` skeletons.

## Assignment mapping

- Data discovery: `scripts/00_discover_data.py`
  - Outputs: `outputs/reports/data_inventory.{csv,md}`, `protocol_artifact_scan.{csv,md}`.
  - Status: complete.
- B3 PCAP parsing/economic decoding: `scripts/01_parse_pcap.py`, `pcap_parser.py`, `b3_decoder.py`, `order_book.py`
  - Outputs: `packet_metadata.csv`, `updates.csv`, `increment_updates.csv`, `snapshot.csv`, `reconstructed_book.csv`, `b3_template_inventory.csv`, `decoded_instruments.csv`, `wdo_instruments.csv`, `wdo_decoded_evidence.csv`.
  - Status: schema-backed decode complete for assignment-critical templates.
- WDO calendar spread: `scripts/02_build_wdo_calendar_spread.py`, `spreads.py`
  - Outputs: `outputs/csv/wdo_top_of_book_timeseries.csv`, `outputs/csv/wdo_calendar_spread.csv`, `outputs/plots/wdo_calendar_spread.png`.
  - Status: computed from decoded B3 WDO MBO order-event time series.
- Volatility/momentum: `scripts/03_compute_vol_momentum.py`, `features.py`
  - Outputs: `volatility_momentum.csv`, `volatility.png`, `momentum.png`.
  - Status: complete for valid quote rows with explicit 400 ms latency.
- Gold arbitrage: `scripts/04_gold_arbitrage_research.py`, `arbitrage.py`
  - Outputs: `gold_arbitrage_signals.csv`, `gold_spread.png`, `gold_spread_zscore.png`, `gold_arbitrage_signals.png`.
  - Status: research prototype complete.
- Validation/tests: `validation.py`, `tests/`
  - Outputs: `validation_report.md`, `summary_metrics.md`.
  - Status: complete.

## B3 protocol provenance
The decoder uses a compatible public schema artifact, `b3-market-data-messages-2.2.0.xml` from `pedrosakuma/B3MarketDataPlatform`, verified against local PCAP frames:

- observed SBE frame header: little-endian `<HHHHHH>` = `msgSize, encoding, blockLen, templateId, schemaId, version`;
- local match: `encoding=0xeb50`, `schemaId=2`, `version=15`;
- packet envelope: channel/feed flag/stream id/packet sequence/sending timestamp, followed by SBE frames from byte offset 16.

Supported decoded templates:

- `12` `SecurityDefinition`;
- `30` `SnapshotFullRefresh_Header`;
- `50` `Order_MBO`;
- `51` `DeleteOrder_MBO`;
- `52` `MassDeleteOrders_MBO`;
- `71` `SnapshotFullRefresh_Orders_MBO`.

Unknown templates remain diagnostic frame evidence and do not populate canonical economic fields.

## Quant methodology summary

### WDO spread
The WDO calendar spread is computed from decoded WDO MBO order-event top-of-book time series, not from the non-WDO quote CSV or a single final book snapshot. The selected contracts (`WDOG26` and `WDOH26`) are adjacent WDO futures with sufficient valid two-sided decoded flow. Rows are filtered to positive non-crossed bid/ask pairs, and near/far books are aligned with a documented `merge_asof` tolerance. The output includes source and schema provenance.

### Volatility/momentum
- Uses valid top-of-book midpoint from quote CSV rows.
- Filters invalid/crossed quotes.
- Computes log returns, 60-second rolling volatility, EWMA volatility, and 30-second momentum z-score.
- Momentum is robust to irregular quote ticks: it uses the last midpoint observed no later than `ts - 30s`, rather than requiring an exact timestamp match.
- Models the 400 ms latency requirement with `decision_ts = ts + 400ms`.
- Uses backward-looking calculations only.

### Gold arbitrage
- Aligns B3 and MOEX gold midquotes by nearest timestamp.
- Computes raw spread.
- Uses shifted rolling mean/std for z-score to avoid look-ahead bias.
- Uses simple threshold mean-reversion signals and spread-point PnL.
- Documents production limitations: FX, multipliers, fees, calendars, stale quotes, execution, and risk.

## Validation controls
Validation checks:

- required output presence;
- row counts and missingness;
- timestamp parsing/ranges/monotonicity;
- duplicate full-row checks;
- B3 decode-status distribution;
- economic fields populated only with schema provenance;
- reconstructed-book bid/ask validity;
- WDO top-of-book time-series non-crossed bid/ask validity;
- WDO spread source, contract names, schema provenance, finite spread, and bid<=ask inputs;
- volatility/momentum latency check;
- volatility/momentum finite-row checks to prevent empty plots from all-NaN features;
- shifted-zscore look-ahead control for arbitrage.

## Remaining limitations
- The decoder intentionally supports only templates required for the assignment-critical path; other templates remain unhandled diagnostics until mapped.
- Full production-grade B3 book reconciliation would additionally need complete exchange recovery/session-state rules, feed A/B reconciliation, auction-state handling, and all template mappings.
- Gold arbitrage is a research prototype, not a production trading system.
- Raw input data is not committed to GitHub.
- Generated large outputs are delivered through Google Drive: https://drive.google.com/drive/folders/1bFTa7zj9hZeBhmgAN0aeZqjb3QWKYxHA

## Submission links
- GitHub repository: https://github.com/xsa-dev/senior-quantitative-researcher-assignment
- Russian Google Doc documentation: https://docs.google.com/document/d/17FHnEeDEcN-3uFHe-J6tAI_y6y9su1lNTST3BWxSLX8/edit?usp=drivesdk
- Google Drive result bundle: https://drive.google.com/drive/folders/1bFTa7zj9hZeBhmgAN0aeZqjb3QWKYxHA

## Recommended wording for employer/interviewer
"I first made the B3 PCAP boundary explicit, then resolved the critical blocker by integrating a compatible B3 UMDF/SBE schema and verifying it against the local PCAP frame headers. The final pipeline decodes real SecurityDefinition and MBO order events, builds a WDO instrument master, reconstructs non-crossed top-of-book rows, computes a full intraday WDO calendar-spread time series with schema provenance, and validates that volatility/momentum features are finite and latency-aware. Unknown templates remain diagnostic; I do not fabricate market fields."
