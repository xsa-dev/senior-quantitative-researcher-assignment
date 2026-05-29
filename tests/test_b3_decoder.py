import struct

import pandas as pd

from quant_assignment.b3_decoder import (
    decode_b3_heuristic,
    decode_b3_schema_backed,
    iter_sbe_frames,
    parse_umdf_packet_header,
)


def test_decoder_keeps_economic_fields_null_for_unparseable_payload():
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
    assert decoded.loc[0, "decode_status"] == "no_sbe_frames"
    assert "WDOF26" in decoded.loc[0, "symbol_candidates_evidence"]
    for col in ["symbol", "message_type", "side", "price", "size", "order_id"]:
        assert pd.isna(decoded.loc[0, col])


def test_parse_umdf_packet_and_sbe_frame_header():
    payload = bytes.fromhex("4e014702000000000ddb95b178087d18100050eb0400020002000f00ec050000")
    header = parse_umdf_packet_header(payload)
    frames = list(iter_sbe_frames(payload))
    assert header.channel == 78
    assert header.stream_id == 583
    assert header.packet_sequence == 0
    assert len(frames) == 1
    assert frames[0].size == 16
    assert frames[0].encoding == 0xEB50
    assert frames[0].template_id == 2
    assert frames[0].schema_id == 2
    assert frames[0].version == 15


def test_schema_backed_decodes_security_definition_and_order():
    sec_id = 200001478883
    instr_body = bytearray(231)
    struct.pack_into("<Q", instr_body, 0, sec_id)
    instr_body[8:12] = b"BVMF"
    instr_body[12:13] = b"8"
    instr_body[13:16] = b"WDO"
    instr_body[16:36] = b"WDOF26" + b"\x00" * 14
    instr_body[36:37] = b"M"
    instr_body[37] = 8
    struct.pack_into("<H", instr_body, 38, 130)
    struct.pack_into("<I", instr_body, 40, 1)
    instr_frame = struct.pack("<HHHHHH", 243, 0xEB50, 231, 12, 2, 15) + bytes(instr_body)

    order_body = bytearray(64)
    struct.pack_into("<Q", order_body, 0, sec_id)
    order_body[8] = 0x80
    order_body[9] = 0  # NEW
    order_body[10] = ord("0")  # BID
    struct.pack_into("<q", order_body, 12, 5_370_0000)
    struct.pack_into("<q", order_body, 20, 3)
    struct.pack_into("<I", order_body, 32, 123)
    struct.pack_into("<Q", order_body, 36, 1764590100059000000)  # mDInsertTimestamp
    struct.pack_into("<Q", order_body, 44, 111222333)
    struct.pack_into("<I", order_body, 52, 7)
    struct.pack_into("<Q", order_body, 56, 1764590100059389321)
    order_frame = struct.pack("<HHHHHH", 76, 0xEB50, 64, 50, 2, 15) + bytes(order_body)

    packet_df = pd.DataFrame([
        {
            "timestamp": pd.Timestamp("2025-01-01", tz="UTC"),
            "source_file": "synthetic/78_Instrument.pcap",
            "packet_index": 0,
            "payload_len": 16 + len(instr_frame),
            "payload_hash": "instr",
            "payload_hex_head": "",
            "payload_bytes": b"\x4e\x00\x00\x00\x01\x00\x00\x00" + b"\x00" * 8 + instr_frame,
        },
        {
            "timestamp": pd.Timestamp("2025-01-01T00:00:01Z"),
            "source_file": "synthetic/78_Incremental_feedA.pcap",
            "packet_index": 1,
            "payload_len": 16 + len(order_frame),
            "payload_hash": "order",
            "payload_hex_head": "",
            "payload_bytes": b"\x4e\x01\x00\x00\x02\x00\x00\x00" + b"\x00" * 8 + order_frame,
        },
    ])
    decoded = decode_b3_schema_backed(packet_df)
    order = decoded[decoded["raw_message_type"] == 50].iloc[0]
    assert order["symbol"] == "WDOF26"
    assert order["side"] == "bid"
    assert order["action"] == "new"
    assert order["price"] == 5370.0
    assert order["size"] == 3
    assert order["order_id"] == 111222333
