from __future__ import annotations
import re
import pandas as pd

_SYMBOL_RE = re.compile(rb"\b[A-Z]{3,6}[FGHJKMNQUVXZ]\d{2}\b|\b[A-Z]{4}\d{1,2}\b|\b[A-Z]{3,6}-\d+\.\d+\b")


def _ascii_symbol_candidates(payload: bytes, limit: int = 8) -> str:
    """Return conservative printable token candidates found in a payload.

    These are evidence tokens only. They are not used to populate the canonical
    `symbol` field because the B3 SBE field offsets/template semantics are not
    available in the repository.
    """
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


def decode_b3_heuristic(packet_df: pd.DataFrame) -> pd.DataFrame:
    """Return an honest normalized baseline without inventing B3 fields.

    The provided data folder does not include official B3 UMDF/SBE XML schema
    templates or a field map. Therefore this function extracts only packet
    envelope candidates and raw evidence that are visible in payload bytes.
    Economically meaningful fields remain null until schema-backed decoding is
    possible.
    """
    rows = []
    for r in packet_df.itertuples(index=False):
        payload = getattr(r, "payload_bytes", b"") or b""
        sequence_number = int.from_bytes(payload[4:8], "little") if len(payload) >= 8 else None
        channel_id = int.from_bytes(payload[2:4], "little") if len(payload) >= 4 else None
        packet_length_candidate = int.from_bytes(payload[0:2], "little") if len(payload) >= 2 else None
        source_file = getattr(r, "source_file", "")
        has_payload = len(payload) > 0
        instrument_payload = "Instrument" in str(source_file)
        decode_status = (
            "instrument_payload_unmapped" if instrument_payload and has_payload
            else "partial_packet_header" if has_payload
            else "no_payload"
        )
        symbol_candidates = _ascii_symbol_candidates(payload) if instrument_payload else ""
        rows.append({
            "timestamp": getattr(r, "timestamp", None),
            "symbol": None,
            "source_file": source_file,
            "packet_index": getattr(r, "packet_index", None),
            "sequence_number": sequence_number,
            "message_type": None,
            "side": None,
            "price": None,
            "size": None,
            "action": "unknown",
            "order_id": None,
            "raw_message_type": None,
            "decode_status": decode_status,
            "channel_id_candidate": channel_id,
            "packet_length_candidate": packet_length_candidate,
            "payload_len": getattr(r, "payload_len", len(payload)),
            "payload_hash": getattr(r, "payload_hash", None),
            "payload_hex_head": getattr(r, "payload_hex_head", payload[:32].hex()),
            "symbol_candidates_evidence": symbol_candidates,
            "notes": (
                "Official B3 UMDF/SBE schema/template mapping was not found. "
                "Only packet envelope candidates and raw payload evidence were extracted. "
                "Canonical price/size/side/symbol/message_type fields are intentionally null."
            ),
        })
    return pd.DataFrame(rows)
