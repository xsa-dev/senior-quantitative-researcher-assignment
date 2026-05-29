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
pytest: 5 passed
```

If the virtual environment already exists, the quick replay is simply:

```bash
make all
```

## 2. Suggested 10-minute demo flow

1. Open `README.md`.
   - Show assignment mapping table.
   - State that the solution is runnable and honest about blocked B3 economic decoding.
2. Open `outputs/reports/protocol_artifact_scan.md`.
   - Show that raw data was re-checked for XML/SBE/template/schema/dictionary/metadata artifacts.
   - Point out: schema/template/XML/SBE files found = 0.
3. Open `outputs/intermediate/packet_metadata.csv`.
   - Show real packet evidence: timestamps, source/destination, ports, payload lengths, payload hashes.
4. Open `outputs/csv/updates.csv`.
   - Show `decode_status`, envelope candidates, payload hash/hex evidence, and intentionally blank economic fields.
5. Open `outputs/csv/reconstructed_book.csv`.
   - Show explicit `not_reconstructed`, not a fake bid/ask book.
6. Open `outputs/csv/wdo_calendar_spread.csv` and `outputs/plots/wdo_calendar_spread.png`.
   - Explain WDO unavailability without fabricated prices.
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

"I separated generic PCAP parsing from B3 economic decoding. The parser reads the captures and emits real packet evidence: timestamps, IP/port metadata, payload sizes, hashes, and payload byte heads. I also record conservative Instrument-payload token evidence, but I do not use it as canonical symbol data. The missing piece is the official B3 UMDF/SBE schema/template and instrument/price-scale/action metadata. Without those, assigning symbol/price/size/side would be fabrication, so the outputs are explicitly marked partial."

## 5. What to say about the B3 blocker

"The blocker is external and precise. I need the B3 UMDF/SBE XML schema/templates, template ID mapping, instrument dictionary/security definitions, price decimal metadata, and snapshot/incremental semantics. The repository has a clean integration point in `b3_decoder.py`; once those files are available, the parser can move from packet evidence to template-level economic events."

## 6. What to say about no fabricated data

"I chose defensible engineering over pretending. There are no fake B3 prices, no fake book levels, no synthetic WDO spread, and no invented template IDs. Unknown fields are null, and each blocked artifact includes `decode_status` and explanatory notes."

## 7. What to say about WDO spread

"The assignment asks for a WDO calendar spread. The supplied quote CSV contains GLDG26 and GOLD-3.26 style symbols, not WDO quote rows. Instrument PCAPs contain WDO-like token evidence, but not decoded prices. Therefore `wdo_calendar_spread.csv` is intentionally empty and the plot is a diagnostic. With WDO quotes or a full B3 decoder, the spread module is ready to align near/far contracts and compute the spread."

## 8. What to say about volatility/momentum and 400 ms latency

"Features are calculated only from information available at or before each quote timestamp. The output includes `decision_ts = ts + 400ms` to make the assumed market-data-to-order latency explicit. This is a research feature table, not a queue-position simulator."

## 9. What to say about gold arbitrage

"The gold arbitrage prototype aligns B3 and MOEX gold midquotes, computes a raw spread, and uses shifted rolling statistics for z-score signals so the current observation does not normalize itself. The PnL is intentionally a spread-point research proxy. Production would require FX conversion, contract multipliers, fees, calendars, stale quote filters, and execution modeling."

## 10. Likely interviewer questions and concise answers

Q: Why didn't you decode B3 prices from the PCAPs?
A: Because the official B3 UMDF/SBE templates, template IDs, instrument dictionary, and price scales are not in the provided data. Decoding prices without those would be guessing.

Q: Did you find anything useful in Instrument PCAPs?
A: Yes, visible ASCII token evidence appears in Instrument payloads. I preserve it as `symbol_candidates_evidence`, but I do not treat it as canonical mapping without schema offsets and field semantics.

Q: Why is the reconstructed book empty/blocked?
A: A book requires trustworthy symbol, side, price, size, action, and sequence semantics. Those are unavailable without the B3 artifacts, so the output explicitly says `not_reconstructed`.

Q: Is the repository still useful?
A: Yes. It is reproducible, validates the provided quote research tasks, preserves PCAP evidence for future decoding, and clearly documents the exact artifacts needed to complete full B3 decoding.
