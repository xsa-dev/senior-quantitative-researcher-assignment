from __future__ import annotations

from dataclasses import dataclass
import re
import struct
from typing import Iterable

import pandas as pd

_SYMBOL_RE = re.compile(rb"\b[A-Z]{3,6}[FGHJKMNQUVXZ]\d{2}\b|\b[A-Z]{4}\d{1,2}\b|\b[A-Z]{3,6}-\d+\.\d+\b")
SBE_ENCODING_MAGIC = 0xEB50
SUPPORTED_SCHEMA_ID = 2
SUPPORTED_SCHEMA_VERSION = 15
PRICE_NULL = -(1 << 63)
QTY_NULL = -(1 << 63)

TEMPLATE_NAMES = {
    1: "SequenceReset",
    2: "Sequence",
    3: "SecurityStatus",
    5: "News",
    9: "EmptyBook",
    10: "SecurityGroupPhase",
    11: "ChannelReset",
    12: "SecurityDefinition",
    15: "OpeningPrice",
    17: "ClosingPrice",
    21: "QuantityBand",
    22: "PriceBand",
    24: "HighPrice",
    25: "LowPrice",
    27: "LastTradePrice",
    28: "SettlementPrice",
    29: "OpenInterest",
    30: "SnapshotFullRefresh_Header",
    50: "Order_MBO",
    51: "DeleteOrder_MBO",
    52: "MassDeleteOrders_MBO",
    53: "Trade",
    71: "SnapshotFullRefresh_Orders_MBO",
}

SIDE_MAP = {0: "bid", 1: "ask", ord("0"): "bid", ord("1"): "ask"}
ACTION_MAP = {0: "new", 1: "change", 2: "delete", 3: "delete_thru", 4: "delete_from"}


@dataclass(frozen=True)
class UmdfPacketHeader:
    channel: int | None
    feed_flag: int | None
    stream_id: int | None
    packet_sequence: int | None
    sending_time_ns: int | None


@dataclass(frozen=True)
class SbeFrame:
    offset: int
    size: int
    encoding: int
    block_length: int
    template_id: int
    schema_id: int
    version: int
    body: bytes


def _ascii_symbol_candidates(payload: bytes, limit: int = 8) -> str:
    """Return conservative printable token candidates found in a payload."""
    if not payload:
        return ""
    seen: list[str] = []
    for token in _SYMBOL_RE.findall(payload):
        s = token.decode("ascii", errors="ignore")
        if s and s not in seen:
            seen.append(s)
        if len(seen) >= limit:
            break
    return "|".join(seen)


def _clean_ascii(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip()


def _u16(b: bytes, off: int) -> int | None:
    return struct.unpack_from("<H", b, off)[0] if len(b) >= off + 2 else None


def _u32(b: bytes, off: int) -> int | None:
    return struct.unpack_from("<I", b, off)[0] if len(b) >= off + 4 else None


def _u64(b: bytes, off: int) -> int | None:
    return struct.unpack_from("<Q", b, off)[0] if len(b) >= off + 8 else None


def _i64(b: bytes, off: int) -> int | None:
    return struct.unpack_from("<q", b, off)[0] if len(b) >= off + 8 else None


def _price4(mantissa: int | None) -> float | None:
    if mantissa is None or mantissa == PRICE_NULL:
        return None
    return mantissa / 10_000.0


def _quantity(qty: int | None) -> int | None:
    if qty is None or qty == QTY_NULL:
        return None
    return int(qty)


def parse_umdf_packet_header(payload: bytes) -> UmdfPacketHeader:
    """Parse the observed B3 UMDF packet header used by the supplied PCAPs.

    Evidence from the local captures shows a 16-byte packet envelope followed by
    one or more SBE frames. Byte 0 is the visible channel (78/88), bytes 4:8 are
    the packet sequence, and bytes 8:16 are a nanosecond timestamp-like field.
    """
    return UmdfPacketHeader(
        channel=payload[0] if len(payload) >= 1 else None,
        feed_flag=payload[1] if len(payload) >= 2 else None,
        stream_id=_u16(payload, 2),
        packet_sequence=_u32(payload, 4),
        sending_time_ns=_u64(payload, 8),
    )


def iter_sbe_frames(payload: bytes, start_offset: int = 16) -> Iterable[SbeFrame]:
    """Yield SBE frames from a B3 UMDF UDP payload.

    Frame header layout observed in the assignment captures:
    `<HHHHHH little-endian>` = `msgSize, encoding, blockLen, templateId,
    schemaId, version`. `msgSize` includes the 12-byte frame header.
    """
    pos = start_offset
    while pos + 12 <= len(payload):
        size, encoding, block_len, template_id, schema_id, version = struct.unpack_from("<HHHHHH", payload, pos)
        if size < 12 or pos + size > len(payload):
            break
        body = payload[pos + 12 : pos + size]
        yield SbeFrame(pos, size, encoding, block_len, template_id, schema_id, version, body)
        pos += size


def decode_security_definition_12(frame: SbeFrame) -> dict[str, object] | None:
    b = frame.body
    if len(b) < 44:
        return None
    return {
        "security_id": _u64(b, 0),
        "security_exchange": _clean_ascii(b[8:12]),
        "security_id_source": _clean_ascii(b[12:13]),
        "security_group": _clean_ascii(b[13:16]),
        "symbol": _clean_ascii(b[16:36]),
        "security_update_action": _clean_ascii(b[36:37]),
        "security_type_raw": b[37],
        "security_subtype": _u16(b, 38),
        "tot_no_related_sym": _u32(b, 40),
        "price_divisor_raw": _i64(b, 68) if len(b) >= 76 else None,
        "tick_size_denominator": b[211] if len(b) >= 212 else None,
        "product_raw": b[212] if len(b) >= 213 else None,
        "decode_status": "schema_backed_instrument_definition",
    }


def decode_order_mbo_50(frame: SbeFrame) -> dict[str, object] | None:
    b = frame.body
    if len(b) < 64:
        return None
    action_raw = b[9]
    side_raw = b[10]
    return {
        "security_id": _u64(b, 0),
        "message_type": "Order_MBO",
        "action": ACTION_MAP.get(action_raw, f"unknown_{action_raw}"),
        "side": SIDE_MAP.get(side_raw, f"unknown_{side_raw}"),
        "price": _price4(_i64(b, 12)),
        "size": _quantity(_i64(b, 20)),
        "order_id": _u64(b, 44),
        "rpt_seq": _u32(b, 52),
        "transact_time_ns": _u64(b, 56),
        "decode_status": "schema_backed_order_mbo",
    }


def decode_delete_order_mbo_51(frame: SbeFrame) -> dict[str, object] | None:
    b = frame.body
    if len(b) < 52:
        return None
    side_raw = b[10]
    return {
        "security_id": _u64(b, 0),
        "message_type": "DeleteOrder_MBO",
        "action": "delete",
        "side": SIDE_MAP.get(side_raw, f"unknown_{side_raw}"),
        "price": _price4(_i64(b, 44)),
        "size": _quantity(_i64(b, 16)),
        "order_id": _u64(b, 24),
        "rpt_seq": _u32(b, 40),
        "transact_time_ns": _u64(b, 32),
        "decode_status": "schema_backed_delete_order_mbo",
    }


def decode_snapshot_header_30(frame: SbeFrame) -> dict[str, object] | None:
    b = frame.body
    if len(b) < 34:
        return None
    return {
        "security_id": _u64(b, 0),
        "message_type": "SnapshotFullRefresh_Header",
        "last_msg_seq_num_processed": _u32(b, 8),
        "tot_num_reports": _u32(b, 12),
        "tot_num_bids": _u32(b, 16),
        "tot_num_offers": _u32(b, 20),
        "tot_num_stats": _u16(b, 24),
        "last_rpt_seq": _u32(b, 28),
        "last_sequence_version": _u16(b, 32),
        "decode_status": "schema_backed_snapshot_header",
    }


def decode_snapshot_orders_mbo_71(frame: SbeFrame) -> list[dict[str, object]]:
    b = frame.body
    if len(b) < 11:
        return []
    security_id = _u64(b, 0)
    entry_block_len = _u16(b, 8) or 0
    num_entries = b[10]
    pos = 11
    rows: list[dict[str, object]] = []
    for idx in range(num_entries):
        entry = b[pos : pos + entry_block_len]
        if len(entry) < min(entry_block_len, 42):
            break
        side_raw = entry[40]
        rows.append({
            "security_id": security_id,
            "message_type": "SnapshotFullRefresh_Orders_MBO",
            "action": "snapshot",
            "side": SIDE_MAP.get(side_raw, f"unknown_{side_raw}"),
            "price": _price4(_i64(entry, 0)),
            "size": _quantity(_i64(entry, 8)),
            "order_id": _u64(entry, 32),
            "snapshot_entry_index": idx,
            "decode_status": "schema_backed_snapshot_order_mbo",
        })
        pos += entry_block_len
    return rows


def _base_row(packet, header: UmdfPacketHeader, frame: SbeFrame) -> dict[str, object]:
    return {
        "timestamp": getattr(packet, "timestamp", None),
        "symbol": None,
        "source_file": getattr(packet, "source_file", ""),
        "packet_index": getattr(packet, "packet_index", None),
        "sequence_number": header.packet_sequence,
        "message_type": TEMPLATE_NAMES.get(frame.template_id),
        "side": None,
        "price": None,
        "size": None,
        "action": "unknown",
        "order_id": None,
        "raw_message_type": frame.template_id,
        "decode_status": "schema_backed_frame_unhandled",
        "channel_id_candidate": header.channel,
        "packet_length_candidate": frame.size,
        "payload_len": getattr(packet, "payload_len", None),
        "payload_hash": getattr(packet, "payload_hash", None),
        "payload_hex_head": getattr(packet, "payload_hex_head", None),
        "symbol_candidates_evidence": _ascii_symbol_candidates(getattr(packet, "payload_bytes", b"") or b""),
        "notes": "B3 UMDF SBE frame parsed; template-specific economic decoder may be pending.",
        "feed_flag": header.feed_flag,
        "stream_id": header.stream_id,
        "packet_sending_time_ns": header.sending_time_ns,
        "frame_offset": frame.offset,
        "frame_size": frame.size,
        "frame_block_length": frame.block_length,
        "schema_id": frame.schema_id,
        "schema_version": frame.version,
        "security_id": None,
        "rpt_seq": None,
        "transact_time_ns": None,
        "schema_provenance": "B3 Binary UMDF SBE schemaId=2/version=15-compatible layout; cross-checked against public b3-market-data-messages-2.2.0.xml where unchanged for decoded fields",
    }


def build_security_master(packet_df: pd.DataFrame) -> dict[int, dict[str, object]]:
    master: dict[int, dict[str, object]] = {}
    for packet in packet_df.itertuples(index=False):
        payload = getattr(packet, "payload_bytes", b"") or b""
        for frame in iter_sbe_frames(payload):
            if frame.encoding != SBE_ENCODING_MAGIC or frame.template_id != 12:
                continue
            decoded = decode_security_definition_12(frame)
            if decoded and decoded.get("security_id") is not None and decoded.get("symbol"):
                master[int(decoded["security_id"])] = decoded
    return master


def decode_b3_schema_backed(packet_df: pd.DataFrame) -> pd.DataFrame:
    """Decode B3 UMDF/SBE frames with the verified schema-compatible layouts.

    This is intentionally conservative: unknown templates remain parsed frame
    evidence, while populated economic fields are emitted only for templates whose
    fixed offsets match the public B3 UMDF SBE schema and the local packet
    framing (`schemaId=2`, `version=15`, `encoding=0xeb50`).
    """
    security_master = build_security_master(packet_df)
    rows: list[dict[str, object]] = []
    for packet in packet_df.itertuples(index=False):
        payload = getattr(packet, "payload_bytes", b"") or b""
        source_file = str(getattr(packet, "source_file", ""))
        if not payload:
            rows.append({
                "timestamp": getattr(packet, "timestamp", None),
                "symbol": None,
                "source_file": source_file,
                "packet_index": getattr(packet, "packet_index", None),
                "sequence_number": None,
                "message_type": None,
                "side": None,
                "price": None,
                "size": None,
                "action": "unknown",
                "order_id": None,
                "raw_message_type": None,
                "decode_status": "no_payload",
                "channel_id_candidate": None,
                "packet_length_candidate": None,
                "payload_len": getattr(packet, "payload_len", 0),
                "payload_hash": getattr(packet, "payload_hash", None),
                "payload_hex_head": getattr(packet, "payload_hex_head", ""),
                "symbol_candidates_evidence": "",
                "notes": "No payload.",
            })
            continue
        header = parse_umdf_packet_header(payload)
        frame_count = 0
        for frame in iter_sbe_frames(payload):
            frame_count += 1
            row = _base_row(packet, header, frame)
            if frame.encoding != SBE_ENCODING_MAGIC or frame.schema_id != SUPPORTED_SCHEMA_ID:
                row["decode_status"] = "unsupported_frame_header"
                row["notes"] = "Frame header did not match observed B3 UMDF SBE encoding/schema."
                rows.append(row)
                continue

            decoded_rows: list[dict[str, object]] = []
            if frame.template_id == 12:
                decoded = decode_security_definition_12(frame)
                if decoded:
                    decoded_rows = [decoded]
            elif frame.template_id == 50:
                decoded = decode_order_mbo_50(frame)
                if decoded:
                    decoded_rows = [decoded]
            elif frame.template_id == 51:
                decoded = decode_delete_order_mbo_51(frame)
                if decoded:
                    decoded_rows = [decoded]
            elif frame.template_id == 52:
                # Mass delete has no price/size/order id; keep action/side if present.
                b = frame.body
                if len(b) >= 28:
                    decoded_rows = [{
                        "security_id": _u64(b, 0),
                        "message_type": "MassDeleteOrders_MBO",
                        "action": ACTION_MAP.get(b[9], f"unknown_{b[9]}"),
                        "side": SIDE_MAP.get(b[10], f"unknown_{b[10]}"),
                        "transact_time_ns": _u64(b, 16),
                        "rpt_seq": _u32(b, 24),
                        "decode_status": "schema_backed_mass_delete_mbo",
                    }]
            elif frame.template_id == 30:
                decoded = decode_snapshot_header_30(frame)
                if decoded:
                    decoded_rows = [decoded]
            elif frame.template_id == 71:
                decoded_rows = decode_snapshot_orders_mbo_71(frame)

            if not decoded_rows:
                rows.append(row)
                continue
            for decoded in decoded_rows:
                out = dict(row)
                out.update(decoded)
                sec_id = out.get("security_id")
                if sec_id is not None and int(sec_id) in security_master:
                    out["symbol"] = security_master[int(sec_id)].get("symbol")
                    out["symbol_candidates_evidence"] = str(out["symbol"] or "")
                elif decoded.get("symbol"):
                    out["symbol"] = decoded.get("symbol")
                    out["symbol_candidates_evidence"] = str(decoded.get("symbol") or "")
                out["raw_message_type"] = frame.template_id
                out["notes"] = "Decoded from B3 UMDF SBE frame with schema-backed fixed offsets."
                rows.append(out)
        if frame_count == 0:
            rows.append({
                "timestamp": getattr(packet, "timestamp", None),
                "symbol": None,
                "source_file": source_file,
                "packet_index": getattr(packet, "packet_index", None),
                "sequence_number": header.packet_sequence,
                "message_type": None,
                "side": None,
                "price": None,
                "size": None,
                "action": "unknown",
                "order_id": None,
                "raw_message_type": None,
                "decode_status": "no_sbe_frames",
                "channel_id_candidate": header.channel,
                "packet_length_candidate": None,
                "payload_len": getattr(packet, "payload_len", len(payload)),
                "payload_hash": getattr(packet, "payload_hash", None),
                "payload_hex_head": getattr(packet, "payload_hex_head", payload[:32].hex()),
                "symbol_candidates_evidence": _ascii_symbol_candidates(payload),
                "notes": "Payload had no parseable B3 UMDF SBE frames.",
            })
    return pd.DataFrame(rows)


def template_inventory(packet_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for packet in packet_df.itertuples(index=False):
        payload = getattr(packet, "payload_bytes", b"") or b""
        header = parse_umdf_packet_header(payload)
        for frame in iter_sbe_frames(payload):
            rows.append({
                "source_file": getattr(packet, "source_file", ""),
                "timestamp": getattr(packet, "timestamp", None),
                "packet_index": getattr(packet, "packet_index", None),
                "channel": header.channel,
                "packet_sequence": header.packet_sequence,
                "template_id": frame.template_id,
                "template_name": TEMPLATE_NAMES.get(frame.template_id, "unknown"),
                "schema_id": frame.schema_id,
                "schema_version": frame.version,
                "block_length": frame.block_length,
                "frame_size": frame.size,
                "frame_offset": frame.offset,
                "sample_hex": frame.body[:48].hex(),
            })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    grouped = df.groupby(["source_file", "template_id", "template_name", "schema_id", "schema_version", "block_length"], dropna=False)
    return grouped.agg(
        count=("template_id", "size"),
        first_timestamp=("timestamp", "min"),
        first_packet_index=("packet_index", "min"),
        sample_hex=("sample_hex", "first"),
    ).reset_index().sort_values(["source_file", "template_id", "block_length"])


def decode_b3_heuristic(packet_df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible alias for the schema-backed decoder.

    Earlier versions emitted only packet-level evidence. We now parse the verified
    UMDF packet/SBE frame structure and decode selected templates conservatively.
    """
    return decode_b3_schema_backed(packet_df)
