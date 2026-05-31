# Interview demo runbook

## 1. Fresh run commands

```bash
cd /Users/alxy/Desktop/1PROJ/senior_quantitative_researcher
make install
make all
```

Expected result:

```text
make all completes
pytest: 14 passed
```

If the virtual environment already exists, the quick replay is simply:

```bash
make all
```

## 2. Suggested 10-minute demo flow

1. Open `README.md`.
   - Show assignment mapping table.
   - State that the solution is runnable, schema-backed for assignment-critical B3 economic fields, and explicit about remaining production limitations.
2. Open `outputs/reports/protocol_artifact_scan.md`.
   - Show that raw data was re-checked for XML/SBE/template/schema/dictionary/metadata artifacts.
   - Point out: schema/template/XML/SBE files found = 0.
3. Open `outputs/intermediate/packet_metadata.csv`.
   - Show real packet evidence: timestamps, source/destination, ports, payload lengths, payload hashes.
4. Open `outputs/csv/updates.csv`.
   - Show schema-backed `decode_status`, `symbol`, `side`, `price`, `size`, `order_id`, template/frame metadata, and provenance.
5. Open `outputs/csv/reconstructed_book.csv`.
   - Show non-crossed reconstructed top-of-book rows where decoded event data is sufficient, and diagnostic rows where full reconstruction is intentionally not claimed.
6. Open `outputs/csv/wdo_top_of_book_timeseries.csv`, `outputs/csv/wdo_calendar_spread.csv`, and `outputs/plots/wdo_calendar_spread.png`.
   - Show decoded event-driven WDO top-of-book replay and the intraday `WDOG26-WDOH26` spread series.
7. Open `outputs/csv/volatility_momentum.csv` and plots.
   - Show `decision_ts = ts + 400ms` and backward-looking features.
8. Open `outputs/csv/gold_arbitrage_signals.csv` and plots.
   - Explain shifted rolling z-score and prototype PnL limitations.
9. Open `outputs/reports/validation_report.md`.
   - Show checks for required outputs, quote sanity, no-fabrication, decode-status distribution, and look-ahead controls.
10. Open `docs/final_submission_summary.md`.
   - Use it as the closing summary.

## 3. Commands to run live

```bash
make discover
make parse-pcap
make validate
make test
```

For a full replay:

```bash
make all
```

## 4. What to say about PCAP parsing

"I separated generic PCAP parsing from B3 economic decoding. The parser reads the captures and emits real packet evidence: timestamps, IP/port metadata, payload sizes, hashes, and payload byte heads. For the assignment-critical economic layer I use a compatible B3 Binary UMDF/SBE schema, verify the frame header against the local PCAPs, and only then populate canonical symbol/side/price/size/order fields with schema provenance. Unsupported templates remain diagnostic evidence instead of guessed data."

## 5. What to say about remaining B3 limitations

"The implemented decoder covers the templates needed for instrument definitions, WDO MBO order events, snapshots, deletes, and the assignment outputs. A production-grade B3 handler would still need complete template coverage, exchange session/recovery rules, auction states, and feed A/B reconciliation. I keep that boundary explicit rather than over-claiming."

## 6. What to say about no fabricated data

"I chose defensible engineering over pretending. Canonical B3 prices, book levels, WDO spreads, and feature tables are emitted only from decoded schema-backed data or from the supplied quote CSV. Unknown templates stay diagnostic, and validation checks assert provenance plus sanity conditions."

## 7. What to say about WDO spread

"Task 2 now uses schema-backed B3 WDO MBO order events. I replay decoded order IDs for the selected adjacent contracts WDOG26 and WDOH26 into a non-crossed top-of-book time series, then align the two contracts with merge_asof to compute an intraday calendar spread. The latest run produces 38,772 WDO top-of-book rows and 21,387 aligned spread rows, with no fabricated prices and explicit schema provenance. WDOF26 is decoded too, but its final local replay state is crossed without full production session/feed reconciliation, so I selected the adjacent pair with clean two-sided flow for a defensible spread series."

## 8. What to say about volatility/momentum and 400 ms latency

"Features are calculated only from information available at or before each quote timestamp. The output includes `decision_ts = ts + 400ms` to make the assumed market-data-to-order latency explicit. Momentum is computed with an as-of 30-second lag, which is robust to irregular tick timestamps and prevents empty all-NaN momentum plots. This is a research feature table, not a queue-position simulator."

## 9. What to say about gold arbitrage

"The gold arbitrage prototype aligns B3 and MOEX gold midquotes, computes a raw spread, and uses shifted rolling statistics for z-score signals so the current observation does not normalize itself. The PnL is intentionally a spread-point research proxy. Production would require FX conversion, contract multipliers, fees, calendars, stale quote filters, and execution modeling."

## 10. Likely interviewer questions and concise answers

Q: Why did you use a compatible public B3 schema instead of hand-decoding bytes?
A: Because prices, sides, sizes, order actions and price scales need template-backed semantics. I verify the SBE frame header against the local captures, then populate economic fields only where schema-backed decoding applies. Unsupported templates remain diagnostic.

Q: Why isn't the book builder production-grade?
A: The assignment needs defensible decoded artifacts and research features. Full production B3 book handling would add complete template coverage, session/recovery state, auction handling and feed reconciliation. I explicitly document that boundary.

Q: Is the repository still useful?
A: Yes. It is reproducible, decodes assignment-critical B3 fields with provenance, computes a real WDO calendar-spread time series, validates quote research tasks, and documents exact limitations.
