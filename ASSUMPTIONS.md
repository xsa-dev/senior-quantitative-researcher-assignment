# ASSUMPTIONS

## Data assumptions
- `documents/` is read-only raw input and is not modified by the pipeline.
- The raw folder contains B3 PCAP/PCAP ZIP captures, `tasks.md`, and one quote CSV: `quotes_202512260854(in).csv`.
- The quote CSV contains GLDG26 and GOLD-3.26 style symbols; no WDO quote rows are present after parsing valid top-of-book records.
- Quote rows with non-positive bid/ask or crossed bid/ask are treated as invalid market-data records and filtered before feature/arbitrage research.

## B3 PCAP assumptions
- No standalone official B3 Binary UMDF/SBE XML schema, SBE template file, field map, template-ID map, or price-scale metadata was found in `documents/`.
- Instrument PCAPs are present and contain visible ASCII security-token evidence, but those payload tokens are not sufficient to populate canonical symbol fields without official template offsets and semantics.
- `packet_length_candidate`, `channel_id_candidate`, and `sequence_number` are byte-level packet-envelope candidates. They are useful protocol evidence, not a claim of complete B3 economic decoding.
- Canonical `symbol`, `message_type`, `side`, `price`, `size`, and `order_id` remain null unless a schema-backed decoder can populate them.

## Quant assumptions
- Volatility and momentum are computed from best bid/ask midpoint because trade/last-price fields are not available in the quotes CSV.
- The 400 ms latency requirement is modeled as `decision_ts = ts + 400ms` and as a no-look-ahead design constraint, not as a full exchange matching/queue simulator.
- Gold arbitrage spread is computed directly between quote midpoints. It is not normalized for FX, contract multipliers, fees beyond a small prototype cost, margin, settlement conventions, or trading-hours overlap.

## WDO assignment assumption
- Since no WDO quote prices are available and B3 PCAP economic prices are not safely decoded, the project emits an explicit unavailable WDO artifact instead of a fabricated spread.
