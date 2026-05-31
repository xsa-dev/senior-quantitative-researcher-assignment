# Quantitative Researcher Assignment Solution

## Interviewer-facing status
This repository is ready to share as an honest, reproducible GitHub solution. It runs locally with `make all`, maps each assignment task to concrete artifacts, and now includes schema-backed B3 Binary UMDF/SBE economic decoding for the assignment-critical path.

The project deliberately separates:

- packet evidence: timestamps, network metadata, payload hashes and frame inventory;
- schema-backed B3 economic fields: symbols, sides, prices, sizes, order ids and message types decoded from verified UMDF/SBE layouts;
- diagnostic-only frames: unhandled templates that remain evidence and never populate canonical market fields.

Latest verified quality gates:

```bash
make all
# parse-pcap: rows 1372832, reconstructed books 2228+, WDO decoded rows 384450, WDO spread rows 21387
make test
# 14 passed
```

See `outputs/reports/validation_report.md` after running the pipeline for exact current counts.

## Project goal
Build a local, reproducible research project for a Quantitative Researcher assignment:

1. Parse B3 PCAP files and decode assignment-critical B3 UMDF/SBE instrument/order-book messages.
2. Build a WDO calendar-spread time series from decoded B3 WDO MBO order events.
3. Compute and plot volatility/momentum for available futures with a 400 ms market-data-to-order latency assumption and irregular-tick-safe momentum.
4. Build a B3-vs-MOEX gold futures arbitrage research prototype from the supplied one-month quotes CSV.

## Repository structure

```text
src/quant_assignment/      parser, B3 decoder, order book, spreads, research, validation
scripts/                   reproducible command-line entrypoints
tests/                     pytest tests for decoder, book replay, spreads, validation and research logic
docs/                      task-level, technical, interview, and final-submission docs
outputs/csv/               generated tables; Git keeps only .gitkeep, full files via Google Drive
outputs/intermediate/      packet metadata and payload samples; Git keeps only .gitkeep
outputs/plots/             generated plots; Git keeps only .gitkeep
outputs/reports/           inventory, protocol provenance, validation reports; Git keeps only .gitkeep
documents/                 raw input data; read-only and git-ignored
```

Generated result artifacts are deliberately excluded from GitHub because several CSV/intermediate files are large. See `docs/results_delivery.md` for the Google Drive delivery contract and target `outputs/` directories.

## Installation

```bash
cd senior-quantitative-researcher-assignment
make install
```

Dependencies are intentionally simple: pandas, numpy, matplotlib, dpkt, pytest.

## Run full pipeline

```bash
make all
```

Equivalent explicit script sequence:

```bash
PYTHONPATH=src .venv/bin/python scripts/00_discover_data.py
PYTHONPATH=src .venv/bin/python scripts/01_parse_pcap.py
PYTHONPATH=src .venv/bin/python scripts/02_build_wdo_calendar_spread.py
PYTHONPATH=src .venv/bin/python scripts/03_compute_vol_momentum.py
PYTHONPATH=src .venv/bin/python scripts/04_gold_arbitrage_research.py
PYTHONPATH=src .venv/bin/python -m quant_assignment.validation
PYTHONPATH=src .venv/bin/python -m pytest -q
```

## Run task targets separately

```bash
make discover      # data inventory + raw-folder protocol scan
make parse-pcap    # B3 frame decode, instrument master, updates, snapshots, reconstructed book
make spread        # WDO calendar spread from schema-backed WDO MBO top-of-book time series
make features      # volatility/momentum feature CSV and plots
make arbitrage     # gold arbitrage signals CSV and plots
make validate      # validation and summary reports
make test          # pytest suite
make all           # all of the above
```

## Assignment mapping and artifacts

- Data discovery
  - Script: `scripts/00_discover_data.py`
  - Outputs: `outputs/reports/data_inventory.{csv,md}`, `protocol_artifact_scan.{csv,md}`
  - Status: complete.
- B3 PCAP parsing and economic decoding
  - Script/code: `scripts/01_parse_pcap.py`, `pcap_parser.py`, `b3_decoder.py`, `order_book.py`
  - Outputs: `updates.csv`, `increment_updates.csv`, `snapshot.csv`, `snapshot_updates.csv`, `reconstructed_book.csv`, `b3_template_inventory.csv`, `decoded_instruments.csv`, `wdo_instruments.csv`, `wdo_decoded_evidence.csv`, `b3_protocol_provenance.md`
  - Status: schema-backed decode complete for assignment-critical templates.
- WDO calendar spread
  - Script/code: `scripts/02_build_wdo_calendar_spread.py`, `spreads.py`
  - Outputs: `outputs/csv/wdo_top_of_book_timeseries.csv`, `outputs/csv/wdo_calendar_spread.csv`, `outputs/plots/wdo_calendar_spread.png`
  - Status: computed as a schema-backed WDO MBO top-of-book time series, then aligned into an intraday calendar-spread series.
- Volatility/momentum
  - Script/code: `scripts/03_compute_vol_momentum.py`, `features.py`
  - Outputs: `volatility_momentum.csv`, `volatility.png`, `momentum.png`
  - Status: complete for available valid quote rows.
- Gold arbitrage
  - Script/code: `scripts/04_gold_arbitrage_research.py`, `arbitrage.py`
  - Outputs: `gold_arbitrage_signals.csv`, `gold_spread.png`, `gold_spread_zscore.png`, `gold_arbitrage_signals.png`
  - Status: research prototype complete.

## B3 PCAP decoding status

The decoder uses a compatible public schema artifact, `b3-market-data-messages-2.2.0.xml` from `pedrosakuma/B3MarketDataPlatform`, and verifies it against local PCAP frames:

- observed frame header: little-endian `<HHHHHH>` = `msgSize, encoding, blockLen, templateId, schemaId, version`;
- local frame match: `encoding=0xeb50`, `schemaId=2`, `version=15`;
- packet envelope: channel/feed flag/stream id/packet sequence/sending timestamp, followed by SBE frames from byte offset 16.

Decoded templates:

- `12` `SecurityDefinition`;
- `30` `SnapshotFullRefresh_Header`;
- `50` `Order_MBO`;
- `51` `DeleteOrder_MBO`;
- `52` `MassDeleteOrders_MBO`;
- `71` `SnapshotFullRefresh_Orders_MBO`.

Unknown templates remain `schema_backed_frame_unhandled` evidence and do not populate economic fields.

## Important CSV schemas

### `updates.csv` / `increment_updates.csv`
Schema-backed B3 event table with `timestamp`, `symbol`, `security_id`, `message_type`, `raw_message_type`, `side`, `price`, `size`, `action`, `order_id`, `rpt_seq`, `schema_id`, `schema_version`, `schema_provenance`, `decode_status` and packet/frame metadata.

### `snapshot.csv` / `snapshot_updates.csv`
Snapshot-compatible decoded rows. Snapshot order rows are decoded where template `71` is present; otherwise rows remain diagnostic.

### `reconstructed_book.csv`
Final non-crossed top-of-book rows reconstructed from decoded MBO events: `bid_price_1`, `bid_size_1`, `ask_price_1`, `ask_size_1`, `mid_price`, `spread`, `book_depth_available`, `decode_status`.

### `wdo_top_of_book_timeseries.csv`
Event-driven non-crossed WDO top-of-book time series replayed from decoded B3 MBO order IDs for the selected spread contracts. Includes bid/ask/mid, top-level sizes, book spread, depth, source, and schema provenance.

### `wdo_calendar_spread.csv`
WDO futures calendar spread from the decoded WDO top-of-book time series. Includes near/far bid/ask/mid, spread, source, and schema provenance.

### `volatility_momentum.csv`
Quote-derived features from valid, non-crossed, positive top-of-book rows: `ret`, `decision_ts`, `rv_1min`, `ewma_vol`, `mom_30s`, `mom_z`. Momentum uses an as-of 30-second lag so irregular tick timestamps produce finite feature values instead of all-NaN plots.

### `gold_arbitrage_signals.csv`
Aligned B3/MOEX gold midpoint research table: `b3_mid`, `moex_mid`, `raw_spread`, shifted rolling `spread_mean`/`spread_std`, `zscore`, `position`, `signal`, `pnl`, `cum_pnl`.

## Validation controls
`make validate` reports:

- required output presence;
- row counts and missing values;
- timestamp parse failures and monotonicity;
- duplicate full rows;
- PCAP `decode_status` distribution;
- economic fields populated only with schema provenance;
- reconstructed-book bid/ask validity;
- WDO spread source/provenance/contract validity and bid<=ask input checks;
- quote sanity: positive bid/ask/mid and no crossed markets;
- volatility/momentum 400 ms latency and finite-feature checks;
- shifted rolling z-score look-ahead control for arbitrage.

## No-fabrication policy
The repository does not invent B3 market data. Canonical symbols, prices, sizes, sides, order ids, message types and WDO spreads are emitted only from schema-backed decoders. Unsupported templates remain diagnostic evidence.

## Known limitations
1. Only assignment-critical B3 templates are economically decoded; other templates remain diagnostic until mapped.
2. Production-grade B3 book building would require full exchange recovery/session-state handling, feed A/B reconciliation and complete template coverage.
3. Gold arbitrage PnL is a spread-point research prototype. Production use requires multipliers, FX normalization, fees, latency/execution modeling, exchange-calendar overlap, stale-quote handling and risk controls.
4. Raw data and generated large artifacts are intentionally not committed to GitHub.

## Interview entry points
- `docs/interview_demo.md` for demo script and talking points.
- `docs/task_1_pcap_parsing.md` for B3 decoding/provenance details.
- `docs/task_2_wdo_calendar_spread.md` for WDO spread methodology and result.
- `docs/final_submission_summary.md` for final assignment mapping.
- `outputs/reports/validation_report.md` for generated evidence of pipeline quality.
