# Task 1 — B3 PCAP parsing

## Outputs
- `outputs/csv/updates.csv`
- `outputs/csv/snapshot.csv`
- `outputs/csv/reconstructed_book.csv`
- `outputs/intermediate/packet_metadata.csv`
- `outputs/intermediate/payload_samples.csv`
- `outputs/reports/protocol_artifact_scan.md`

## Implemented layers
1. Raw file/archive discovery, including nested ZIP entry listing.
2. Direct `.pcap` reading plus `.pcap.zip` support without modifying raw files.
3. Ethernet/IP/UDP/TCP extraction via `dpkt`.
4. Packet evidence extraction: timestamp, source/destination IPs and ports, payload length, payload SHA-256, payload hex head.
5. Packet-envelope candidates: length/channel/sequence bytes.
6. Instrument payload evidence: conservative ASCII security-token candidates are recorded in `symbol_candidates_evidence` for Instrument PCAP packets.
7. Normalized assignment schemas for updates, snapshots, and top-of-book table.
8. Validation of PCAP output decode-status distribution and no-fabrication rules.

## What was actually decoded or extracted
- PCAP timestamps.
- L3/L4 metadata: protocol, IPs, ports.
- Payload length/hash/first bytes.
- Packet-level candidate fields: `packet_length_candidate`, `channel_id_candidate`, `sequence_number`.
- `decode_status`:
  - `partial_packet_header` for non-Instrument payloads where only envelope evidence is extracted.
  - `instrument_payload_unmapped` for Instrument payloads that contain token evidence but lack schema-backed field interpretation.
  - `no_payload` if a packet has no payload.
- Evidence-only `symbol_candidates_evidence` for Instrument payloads.

## What was not decoded
The following canonical economic fields remain null/unknown by design:

- `symbol`
- `message_type`
- `raw_message_type`
- `side`
- `price`
- `size`
- `order_id`
- book level/action semantics beyond `action=unknown`

## Why full economic decoding is blocked
The raw folder was re-checked for XML/SBE/template/schema/security-definition/instrument-dictionary/metadata files. `outputs/reports/protocol_artifact_scan.md` reports:

- candidate protocol-related files/entries: PCAPs, PCAP ZIPs, quote CSV;
- schema/template/XML/SBE files found: 0.

The folder contains B3 Instrument/Snapshot/Incremental PCAP payload captures, and Instrument payloads visibly contain security-like ASCII tokens. However, without the official B3 message templates and field offsets, those tokens cannot safely establish the canonical symbol for each market-data event or decode the price/size/side/action fields.

## Exact external artifacts required
To complete full B3 economic decoding, provide:

1. B3 UMDF/SBE XML schema/templates for the relevant feed/date/channel.
2. Template ID to message-type mapping.
3. Instrument/security definition dictionary and symbol mapping.
4. Price scale/decimal metadata for each price field.
5. Snapshot/incremental action semantics: add, change, delete, clear, implied/regular book behavior, level/order-id rules.
6. Sequence/reset/channel reconciliation rules for feed A/B, snapshots, incrementals, and instrument definitions.

## How the code is structured for completion
- `src/quant_assignment/pcap_parser.py` handles packet extraction and can remain unchanged.
- `src/quant_assignment/b3_decoder.py` is the integration point for schema-backed template decoding.
- `src/quant_assignment/order_book.py` is ready to consume decoded `symbol`, `side`, `price`, `size`, `level`, and `action` fields.
- `scripts/01_parse_pcap.py` already writes the required update/snapshot/book artifacts.
- `src/quant_assignment/validation.py` will flag any populated economic fields, which should remain null until they are backed by verified mappings.

## No-fabrication guarantee
The current generated outputs contain useful packet evidence but no invented market data. `reconstructed_book.csv` emits an explicit `not_reconstructed` row rather than fake bid/ask levels. WDO spreads are not synthesized from Instrument-token evidence.

## Interview wording
"I made Task 1 defensible by separating packet parsing from economic decoding. The parser proves that the PCAPs are read and preserves payload-level evidence. The remaining blocker is external: the official B3 UMDF/SBE templates and instrument/price-scale metadata are not in the provided folder. I recorded Instrument payload token evidence but intentionally left canonical symbol/price/size/side null because assigning them without template offsets would fabricate market data."
