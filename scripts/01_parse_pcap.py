#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from quant_assignment.pcap_parser import parse_pcap_bytes
from quant_assignment.b3_decoder import decode_b3_schema_backed, template_inventory
from quant_assignment.order_book import build_snapshot_updates, reconstruct_book


def iter_selected_pcap_files(data_dir: Path):
    """Yield local PCAP files, applying skips before loading bytes into memory."""
    for p in sorted(data_dir.rglob('*.pcap')):
        src = str(p)
        # The 88 incremental captures are ~10GB each. They are useful for later
        # full-scale decoding, but the assignment baseline stays reproducible by
        # using the smaller 78 channel plus 78/88 snapshots/instruments.
        if 'Incremental' in src and '88_' in src:
            continue
        yield p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-dir', default='documents')
    ap.add_argument('--output-dir', default='outputs')
    ap.add_argument('--max-packets-per-file', type=int, default=200000)
    args = ap.parse_args()

    data = Path(args.data_dir)
    out = Path(args.output_dir)
    (out / 'csv').mkdir(parents=True, exist_ok=True)
    (out / 'intermediate').mkdir(parents=True, exist_ok=True)
    (out / 'reports').mkdir(parents=True, exist_ok=True)

    frames = []
    for path in iter_selected_pcap_files(data):
        try:
            frames.append(parse_pcap_bytes(str(path), path.read_bytes(), max_packets=args.max_packets_per_file))
        except Exception as e:
            print('parse err', path, e)

    packets = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=[
        'timestamp', 'source_file', 'packet_index', 'protocol', 'src_ip', 'dst_ip',
        'src_port', 'dst_port', 'payload_len', 'payload_hash', 'payload_hex_head', 'payload_bytes'
    ])
    packets.to_csv(out / 'intermediate/packet_metadata.csv', index=False)
    sample_cols = [c for c in ['source_file', 'packet_index', 'payload_len', 'payload_hex_head', 'payload_hash'] if c in packets.columns]
    packets[sample_cols].head(5000).to_csv(out / 'intermediate/payload_samples.csv', index=False)

    inv = template_inventory(packets)
    inv.to_csv(out / 'reports/b3_template_inventory.csv', index=False)

    decoded = decode_b3_schema_backed(packets)
    updates, snapshot = build_snapshot_updates(decoded)
    book = reconstruct_book(decoded)

    updates.to_csv(out / 'csv/updates.csv', index=False)
    updates[updates['source_file'].astype(str).str.contains('Incremental', na=False)].to_csv(out / 'csv/increment_updates.csv', index=False)
    updates[updates['source_file'].astype(str).str.contains('Snapshot', na=False)].to_csv(out / 'csv/snapshot_updates.csv', index=False)
    snapshot.to_csv(out / 'csv/snapshot.csv', index=False)
    book.to_csv(out / 'csv/reconstructed_book.csv', index=False)

    wdo = decoded[decoded['symbol'].fillna('').astype(str).str.startswith('WDO')]
    wdo.to_csv(out / 'reports/wdo_decoded_evidence.csv', index=False)
    print('rows', len(updates), len(snapshot), len(book), 'wdo_rows', len(wdo), 'templates', len(inv))


if __name__ == '__main__':
    main()
