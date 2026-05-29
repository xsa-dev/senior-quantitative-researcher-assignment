# Results delivery

Generated result files are intentionally **not committed to GitHub**.

Reason: the assignment outputs include large CSV/PCAP-derived artifacts (`updates.csv`, `snapshot.csv`, `packet_metadata.csv`, raw `documents/`) that exceed normal GitHub limits and should be delivered through Google Drive or another external file store.

## Repository layout

The repository keeps only the output directory skeleton:

```text
outputs/
  .gitkeep
  csv/.gitkeep
  intermediate/.gitkeep
  plots/.gitkeep
  reports/.gitkeep
```

After running the pipeline locally, or after downloading the shared result bundle from Google Drive, place files into these directories:

```text
outputs/csv/            final CSV tables for the assignment
outputs/intermediate/   packet metadata and payload evidence tables
outputs/plots/          generated PNG plots
outputs/reports/        validation, inventory, and protocol-scan reports
```

## Expected generated artifacts

### `outputs/csv/`

- `updates.csv` — packet-derived update/event table; economic B3 fields stay null without official protocol artifacts.
- `snapshot.csv` — snapshot-compatible table; economic B3 fields stay null without official protocol artifacts.
- `reconstructed_book.csv` — explicit blocked top-of-book artifact when schema-backed reconstruction is unavailable.
- `wdo_calendar_spread.csv` — WDO spread artifact; empty diagnostic if WDO prices are unavailable.
- `volatility_momentum.csv` — quote-derived volatility/momentum feature table.
- `gold_arbitrage_signals.csv` — aligned B3/MOEX gold arbitrage research table.

### `outputs/intermediate/`

- `packet_metadata.csv` — packet timestamps, ports, payload lengths, hashes, and hex heads.
- `payload_samples.csv` — compact payload evidence samples.

### `outputs/plots/`

- `wdo_calendar_spread.png`
- `volatility.png`
- `momentum.png`
- `gold_spread.png`
- `gold_spread_zscore.png`
- `gold_arbitrage_signals.png`

### `outputs/reports/`

- `data_inventory.csv`
- `data_inventory.md`
- `protocol_artifact_scan.csv`
- `protocol_artifact_scan.md`
- `validation_report.md`
- `summary_metrics.md`

## Recreate locally

```bash
make install
make all
```

The pipeline will regenerate the files under `outputs/` from local raw input data in `documents/`.

## Google Drive checklist before submission

1. Run `make all` successfully.
2. Upload generated `outputs/csv/`, `outputs/intermediate/`, `outputs/plots/`, and `outputs/reports/` files to Google Drive.
3. Upload or separately share raw assignment files from `documents/` only if the interviewer expects them and access policy allows it.
4. Insert Google Drive links into the final submission document / Google Doc.
5. Keep GitHub focused on code, docs, tests, reproducibility commands, and this output-directory contract.
