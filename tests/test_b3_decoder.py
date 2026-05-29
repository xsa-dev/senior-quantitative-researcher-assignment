import pandas as pd

from quant_assignment.b3_decoder import decode_b3_heuristic


def test_decoder_keeps_economic_fields_null_without_schema():
    packet_df = pd.DataFrame([
        {
            "timestamp": pd.Timestamp("2025-01-01", tz="UTC"),
            "source_file": "documents/20251201/78_Instrument.pcap",
            "packet_index": 0,
            "payload_len": 32,
            "payload_hash": "abc",
            "payload_hex_head": "",
            "payload_bytes": b"\x4e\x00\xdf\x5c\x01\x00\x00\x00WDOF26\x00DOLAR MINI",
        }
    ])
    decoded = decode_b3_heuristic(packet_df)
    assert decoded.loc[0, "decode_status"] == "instrument_payload_unmapped"
    assert "WDOF26" in decoded.loc[0, "symbol_candidates_evidence"]
    for col in ["symbol", "message_type", "side", "price", "size", "order_id"]:
        assert pd.isna(decoded.loc[0, col])
