# Technical Documentation

## Architecture

```text
scripts/00_discover_data.py              raw inventory + protocol-artifact scan
scripts/01_parse_pcap.py                 PCAP packet extraction + honest partial decoder
scripts/02_build_wdo_calendar_spread.py  WDO spread artifact/diagnostic
scripts/03_compute_vol_momentum.py       volatility and momentum research features
scripts/04_gold_arbitrage_research.py    B3/MOEX gold arbitrage prototype
src/quant_assignment/pcap_parser.py      dpkt packet reader
src/quant_assignment/b3_decoder.py       schema integration point; currently honest partial decoder
src/quant_assignment/order_book.py       snapshot/book construction from decoded events
src/quant_assignment/spreads.py          quote loading, quote sanity filters, spread logic
src/quant_assignment/features.py         backward-looking feature calculations
src/quant_assignment/arbitrage.py        shifted-zscore arbitrage prototype
src/quant_assignment/validation.py       output validation/reporting
```

## Data flow

1. `make discover`
   - inventories raw files and ZIP entries;
   - scans for XML/SBE/template/schema/security-definition/instrument-dictionary/metadata artifacts;
   - writes `outputs/reports/data_inventory.{csv,md}` and `protocol_artifact_scan.{csv,md}`.
2. `make parse-pcap`
   - parses Ethernet/IP/UDP/TCP packets from B3 PCAP files;
   - writes packet evidence to `outputs/intermediate/packet_metadata.csv` and `payload_samples.csv`;
   - extracts only payload-visible envelope candidates;
   - writes `updates.csv`, `snapshot.csv`, `reconstructed_book.csv`.
3. `make spread`
   - loads quote CSV;
   - filters invalid/crossed quotes;
   - emits WDO spread if at least two WDO contracts exist;
   - otherwise emits an empty CSV plus diagnostic plot/note.
4. `make features`
   - computes midpoint returns, rolling realized volatility, EWMA volatility, 30-second momentum, and momentum z-score;
   - adds `decision_ts = ts + 400ms`.
5. `make arbitrage`
   - aligns B3 and MOEX gold midpoints using nearest timestamp;
   - computes raw spread and shifted rolling z-score;
   - creates simple mean-reversion signals and spread-point PnL.
6. `make validate` and `make test`
   - validate generated outputs and run unit tests.

## B3 PCAP decoder design

The decoder intentionally has two layers:

- packet/parser layer: real and complete for generic PCAP metadata;
- economic decoder layer: blocked until B3 schema artifacts are provided.

Current `decode_status` values:

- `partial_packet_header`: payload exists; only envelope candidates were extracted.
- `instrument_payload_unmapped`: Instrument PCAP payload with evidence tokens but no schema-backed interpretation.
- `not_reconstructed`: book reconstruction blocked because canonical economic fields are unavailable.

When official artifacts are provided, add a schema-backed decoder in `b3_decoder.py` that:

1. reads the SBE XML/template definitions;
2. identifies packet/message boundaries and template IDs;
3. decodes template-specific fields;
4. joins instrument/security definitions to canonical symbols;
5. applies price decimal/scale metadata;
6. maps snapshot/incremental action semantics;
7. passes decoded events to `order_book.py`.

## Quote and spread methods

- The quote loader drops rows with invalid timestamps/symbols, non-positive bid/ask, and crossed top-of-book quotes.
- WDO spread uses nearest-timestamp alignment with a bounded tolerance when two WDO contracts exist.
- If WDO prices are unavailable, the output is intentionally empty and documented.

## Volatility/momentum methods

- Midpoint = `(bid_price + ask_price) / 2` after quote sanity filtering.
- Return = log midpoint difference.
- Realized volatility = rolling 60-second standard deviation of returns, annualized with an intraday scaling approximation.
- EWMA volatility = exponentially weighted return standard deviation.
- Momentum = 30-second percentage change and rolling z-score.
- Latency = `decision_ts = ts + 400ms`.

## Gold arbitrage methods

- B3 leg: GLD-like futures symbol from quote CSV.
- MOEX leg: GOLD-like symbol from quote CSV.
- Alignment: nearest timestamp within 2 seconds.
- Signal: mean reversion on shifted rolling z-score.
- PnL: previous position times spread change minus prototype transaction cost.

## Validation

Validation report covers:

- required outputs;
- row counts/missingness;
- duplicate full rows;
- timestamp parsing/ranges/monotonicity;
- quote sanity;
- spread sanity;
- PCAP `decode_status` distribution;
- no fabricated canonical B3 economic fields;
- order-book validity when both bid and ask are known;
- volatility/momentum latency check;
- arbitrage look-ahead-bias controls.

## Testing

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
```

Current suite includes spread, feature, arbitrage, order-book, and B3 decoder no-fabrication tests.
