# DECISIONS

## 1. Be honest about PCAP decoding
The B3 PCAP parser extracts packet metadata, payload hashes, payload hex heads, packet-envelope candidates, and B3 UMDF/SBE frames. Canonical economic fields (`symbol`, `side`, `price`, `size`, `message_type`, and `order_id`) are populated only for schema-backed decoded templates; still-unmapped templates remain diagnostic and do not invent fields.

## 2. Treat Instrument PCAP tokens as evidence only
Instrument PCAP payloads visibly contain security-like ASCII tokens. The code records these in `symbol_candidates_evidence` for audit/debugging, but does not assign them to canonical `symbol` because template offsets, field identities, validity periods, price scale, and action semantics are not available.

## 3. Preserve raw packet evidence
`outputs/intermediate/packet_metadata.csv` and `payload_samples.csv` preserve timestamps, ports, payload lengths, payload hashes, and payload hex heads so future protocol work can continue from reproducible evidence without changing raw files.

## 4. Keep artifacts honest
For partially supported templates, the pipeline emits schema-valid diagnostic rows instead of fake data. Assignment-critical WDO spread artifacts now use schema-backed decoded WDO MBO order-event replay (`wdo_top_of_book_timeseries.csv`) and aligned calendar spread rows (`wdo_calendar_spread.csv`) rather than fabricated prices.

## 5. Avoid look-ahead bias
- Feature calculations are backward-looking.
- Volatility/momentum expose `decision_ts = ts + 400ms`.
- Arbitrage z-score uses shifted rolling statistics.
- Strategy PnL uses the previous position.

## 6. Keep one-command reproducibility
All generated outputs are recreated by `make all`, and each individual task target is callable from the Makefile.

## 7. Validate defensibility, not cosmetic completeness
Validation checks output presence, missingness, timestamps, duplicates, quote sanity, PCAP decode-status distribution, schema provenance for populated PCAP economic fields, reconstructed-book bid/ask validity where known, WDO time-series/spread non-crossed inputs, and look-ahead-bias controls.
