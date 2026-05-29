# Task 1 — B3 PCAP parsing and schema-backed economic decoding

## Outputs
- `outputs/csv/updates.csv`
- `outputs/csv/increment_updates.csv`
- `outputs/csv/snapshot.csv`
- `outputs/csv/snapshot_updates.csv`
- `outputs/csv/reconstructed_book.csv`
- `outputs/intermediate/packet_metadata.csv`
- `outputs/intermediate/payload_samples.csv`
- `outputs/reports/b3_template_inventory.csv`
- `outputs/reports/decoded_instruments.csv`
- `outputs/reports/wdo_instruments.csv`
- `outputs/reports/b3_protocol_provenance.md`
- `outputs/reports/wdo_decoded_evidence.csv`

## Protocol provenance
The economic decoder is no longer regex-only packet evidence. It uses a public B3 UMDF/SBE-compatible schema artifact, `b3-market-data-messages-2.2.0.xml`, from `pedrosakuma/B3MarketDataPlatform`, then verifies it against the local PCAP framing:

- local SBE frame header: little-endian `<HHHHHH>` = `msgSize, encoding, blockLen, templateId, schemaId, version`;
- local frame match: `encoding=0xeb50`, `schemaId=2`, `version=15`;
- packet envelope: channel/feed flag/stream id/packet sequence/sending timestamp, followed by SBE frames starting at byte offset 16.

The generated `outputs/reports/b3_protocol_provenance.md` records the exact run-level counts and supported templates.

## Decoded templates
The decoder populates economic fields only for templates with schema-backed fixed offsets:

- `12` — `SecurityDefinition`: `security_id`, canonical `symbol`, exchange/source/group and instrument metadata.
- `30` — `SnapshotFullRefresh_Header`: snapshot sequence and report counters.
- `50` — `Order_MBO`: action, side, price, size, order id, report sequence and transaction timestamp.
- `51` — `DeleteOrder_MBO`: delete side, price, size, order id and sequence fields.
- `52` — `MassDeleteOrders_MBO`: instrument/side-level mass delete semantics.
- `71` — `SnapshotFullRefresh_Orders_MBO`: snapshot order rows.

Unknown templates remain diagnostic frame evidence (`schema_backed_frame_unhandled`) and do not fabricate symbol/price/size/side/order fields.

## Instrument master and WDO evidence
`SecurityDefinition` messages build a real instrument master in `outputs/reports/decoded_instruments.csv`. `outputs/reports/wdo_instruments.csv` filters canonical WDO futures symbols from that master, and `outputs/reports/wdo_decoded_evidence.csv` contains decoded WDO MBO events.

On the latest full run, the pipeline decoded WDO futures including `WDOF26`, `WDOG26`, and `WDOH26`, with real security ids and decoded order-book events.

## Order-book reconstruction
`src/quant_assignment/order_book.py` replays decoded MBO events deterministically:

- `new`/`change` upsert an order by `order_id`;
- `delete` removes a specific order;
- mass-delete messages without an order id clear the decoded side for that instrument;
- best bid = max active bid price;
- best ask = min active ask price;
- best sizes are aggregated at the best level.

Crossed final top-of-book rows are excluded from the final reconstructed-book output rather than used downstream. This avoids feeding auction/uncleared replay states into the WDO spread.

## No-fabrication guarantee
The code never invents market fields. Canonical `symbol`, `price`, `size`, `side`, `order_id`, and `message_type` are populated only from schema-backed template decoders and carry `schema_provenance`. Otherwise fields remain null or diagnostic-only.
