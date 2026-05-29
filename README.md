# Quantitative Researcher Assignment Solution

## Interviewer-facing status
This repository is ready to share as an honest, reproducible GitHub solution. It runs locally from scratch, maps each assignment task to concrete artifacts, and explicitly separates:

- real decoded/parsed evidence: packet metadata, timestamps, ports, payload hashes, quote-derived research outputs;
- partial B3 payload evidence: channel/sequence/length candidates and ASCII instrument-token evidence from Instrument PCAP payloads;
- unavailable B3 economic fields: canonical symbol, side, price, size, order id, message type, and reconstructed order book.

The key technical blocker is not hidden: full B3 PCAP economic decoding requires external protocol artifacts that are not present in `documents/`.

Latest verified quality gates:

```bash
make all
# pytest: 5 passed
```

## Project goal
Build a local, reproducible research project for a Quantitative Researcher assignment:

1. Parse B3 PCAP files into packet evidence, update/snapshot schemas, and reconstructed-book status.
2. Build a WDO calendar-spread artifact when WDO futures prices are available.
3. Compute and plot volatility/momentum for available futures with a 400 ms market-data-to-order latency assumption.
4. Build a B3-vs-MOEX gold futures arbitrage research prototype from the supplied one-month quotes CSV.

## Repository structure

```text
src/quant_assignment/      core parser, decoder, research, validation modules
scripts/                   reproducible command-line entrypoints
tests/                     pytest tests, including no-fabrication PCAP decoder test
docs/                      task-level, technical, interview, and final-submission docs
outputs/csv/               generated tables; Git keeps only .gitkeep, full files via Google Drive
outputs/intermediate/      packet metadata and payload samples; Git keeps only .gitkeep
outputs/plots/             generated plots; Git keeps only .gitkeep
outputs/reports/           inventory, protocol scan, validation reports; Git keeps only .gitkeep
documents/                 raw input data; read-only and git-ignored
```

Generated result artifacts are deliberately excluded from GitHub because several CSV/intermediate files are larger than normal GitHub limits. See `docs/results_delivery.md` for the Google Drive delivery contract and the exact target directories under `outputs/`.

## Installation

```bash
cd /Users/alxy/Desktop/1PROJ/senior_quantitative_researcher
make install
```

The current host uses Python 3.9.6. Dependencies are intentionally simple: pandas, numpy, matplotlib, dpkt, pytest.

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
make discover      # data inventory + protocol artifact scan
make parse-pcap    # PCAP packet metadata, updates, snapshot, reconstructed-book status
make spread        # WDO calendar spread artifact or explicit unavailable diagnostic
make features      # volatility/momentum feature CSV and plots
make arbitrage     # gold arbitrage signals CSV and plots
make validate      # validation and summary reports
make test          # pytest suite
make all           # all of the above
```

## Assignment mapping and artifacts

| Assignment task | Script | Main output | Supporting output | Current status |
|---|---|---|---|---|
| Data discovery | `scripts/00_discover_data.py` | `outputs/reports/data_inventory.csv` | `data_inventory.md`, `protocol_artifact_scan.{csv,md}` | Complete |
| B3 PCAP parsing | `scripts/01_parse_pcap.py` | `outputs/csv/updates.csv`, `snapshot.csv`, `reconstructed_book.csv` | `outputs/intermediate/packet_metadata.csv`, `payload_samples.csv` | Partial economic decode; blocker documented |
| WDO calendar spread | `scripts/02_build_wdo_calendar_spread.py` | `outputs/csv/wdo_calendar_spread.csv` | `outputs/plots/wdo_calendar_spread.png` | No WDO quote prices available; empty diagnostic artifact, not fabricated |
| Volatility/momentum | `scripts/03_compute_vol_momentum.py` | `outputs/csv/volatility_momentum.csv` | `outputs/plots/volatility.png`, `momentum.png` | Complete for available liquid symbol |
| Gold arbitrage | `scripts/04_gold_arbitrage_research.py` | `outputs/csv/gold_arbitrage_signals.csv` | `outputs/plots/gold_spread.png`, `gold_spread_zscore.png`, `gold_arbitrage_signals.png` | Research prototype complete |
| Validation | `src/quant_assignment/validation.py` | `outputs/reports/validation_report.md` | `outputs/reports/summary_metrics.md` | Complete |

## B3 PCAP decoding status

`documents/` was scanned for XML/SBE/template/schema/security-definition/instrument-dictionary/metadata files. Result: no standalone B3 UMDF/SBE schema/template file, template-ID map, price-scale table, or decoded instrument dictionary file was found.

The folder does include Instrument/Snapshot/Incremental PCAP captures. The Instrument PCAPs visibly contain ASCII security tokens such as WDO-like futures tokens, so the decoder records `symbol_candidates_evidence` for Instrument payloads. These evidence tokens are not used to populate canonical `symbol`, because without official template offsets and field semantics that would be unsafe.

Needed external artifacts for full economic decoding:

1. B3 UMDF/SBE XML schema/templates.
2. Template ID to message-type mapping.
3. Instrument/security definition dictionary and symbol mapping.
4. Price scale/decimal metadata for every price field.
5. Snapshot and incremental action semantics: add/modify/delete/clear, level/order id behavior, sequence/reset rules.
6. Channel/feed mapping and recovery/snapshot reconciliation rules.

## No-fabrication policy

The repository deliberately does not invent:

- B3 prices;
- B3 sizes;
- B3 bid/ask levels;
- WDO calendar-spread values;
- protocol template IDs or message types;
- instrument mappings.

Blocked fields are null/unknown and accompanied by `decode_status` and `notes`. `reconstructed_book.csv` contains an explicit `not_reconstructed` row instead of a fake book.

## Important CSV schemas

### `updates.csv`
Packet-derived normalized event table. Economic fields remain blank until schema-backed decoding is available.

Key columns: `timestamp`, `source_file`, `packet_index`, `sequence_number`, `channel_id_candidate`, `packet_length_candidate`, `payload_len`, `payload_hash`, `payload_hex_head`, `symbol_candidates_evidence`, `decode_status`, `notes`.

### `snapshot.csv`
Snapshot-compatible table with `timestamp`, `symbol`, `side`, `price`, `size`, `level`, `decode_status`, `notes`. Price/size/side/level are intentionally blank without a schema-backed decode.

### `reconstructed_book.csv`
Top-of-book schema. In the current dataset it contains one explicit blocked row: `decode_status=not_reconstructed`.

### `volatility_momentum.csv`
Quote-derived features from valid, non-crossed, positive top-of-book rows: `ret`, `decision_ts`, `rv_1min`, `ewma_vol`, `mom_30s`, `mom_z`.

### `gold_arbitrage_signals.csv`
Aligned B3/MOEX gold midpoint research table: `b3_mid`, `moex_mid`, `raw_spread`, shifted rolling `spread_mean`/`spread_std`, `zscore`, `position`, `signal`, `pnl`, `cum_pnl`.

## Validation controls

`make validate` reports:

- required output presence;
- row counts and missing values;
- timestamp parse failures and monotonicity;
- duplicate full rows;
- PCAP `decode_status` distribution;
- no-fabrication checks for canonical B3 economic fields;
- order book bid/ask validity when both sides are known;
- quote sanity: positive bid/ask/mid and no crossed markets;
- WDO unavailability reason;
- volatility/momentum 400 ms latency check;
- shifted rolling z-score look-ahead control for arbitrage.

## Look-ahead bias controls

- Volatility/momentum are computed from current and past observations only.
- `decision_ts = ts + 400ms` makes the latency assumption explicit.
- Gold arbitrage rolling mean/std are shifted by one observation before z-score calculation.
- Gold PnL uses previous position versus observed spread change.

## Known limitations

1. Full B3 order-book decoding requires external B3 protocol artifacts not present in `documents/`.
2. WDO calendar spread cannot be economically computed from the current data: no WDO rows exist in the supplied quote CSV and PCAP prices are unavailable without schema-backed decoding.
3. Gold arbitrage PnL is a spread-point research prototype. Production use requires contract multipliers, FX normalization, fees, latency/execution modeling, exchange-calendar overlap, stale-quote handling, and risk controls.
4. Raw data and large intermediate packet artifacts are intentionally not suitable for direct GitHub commit.

## Interview entry points

- `docs/interview_demo.md` for demo script and talking points.
- `docs/task_1_pcap_parsing.md` for PCAP blocker and no-fabrication explanation.
- `docs/final_submission_summary.md` for final assignment mapping.
- `outputs/reports/validation_report.md` for generated evidence of pipeline quality.
