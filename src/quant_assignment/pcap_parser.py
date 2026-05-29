from __future__ import annotations
import hashlib, io, zipfile
from pathlib import Path
from typing import Iterable
import dpkt
import pandas as pd


def iter_pcap_sources(data_dir: Path) -> Iterable[tuple[str, bytes]]:
    seen = {p.name for p in data_dir.rglob('*.pcap')}
    for p in sorted(data_dir.rglob("*.pcap")):
        yield str(p), p.read_bytes()
    for z in sorted(data_dir.rglob("*.pcap.zip")):
        with zipfile.ZipFile(z) as zz:
            for n in zz.namelist():
                if n.endswith('.pcap') and Path(n).name not in seen:
                    yield f"{z}::{n}", zz.read(n)

def parse_pcap_bytes(source: str, raw: bytes, max_packets: int | None = None) -> pd.DataFrame:
    reader = dpkt.pcap.Reader(io.BytesIO(raw))
    rows=[]
    for i,(ts,buf) in enumerate(reader):
        if max_packets and i>=max_packets: break
        try:
            eth=dpkt.ethernet.Ethernet(buf); ip=eth.data
            if not isinstance(ip, dpkt.ip.IP): continue
            l4=ip.data
            if isinstance(l4, dpkt.udp.UDP): proto='UDP'; sport,dport,payload=l4.sport,l4.dport,bytes(l4.data)
            elif isinstance(l4, dpkt.tcp.TCP): proto='TCP'; sport,dport,payload=l4.sport,l4.dport,bytes(l4.data)
            else: continue
            rows.append({
                'timestamp': pd.to_datetime(float(ts), unit='s', utc=True),
                'source_file': source,
                'packet_index': i,
                'protocol': proto,
                'src_ip': '.'.join(map(str,ip.src)),
                'dst_ip': '.'.join(map(str,ip.dst)),
                'src_port': sport,
                'dst_port': dport,
                'payload_len': len(payload),
                'payload_hash': hashlib.sha256(payload).hexdigest(),
                'payload_hex_head': payload[:32].hex(),
                'payload_bytes': payload,
            })
        except Exception as e:
            rows.append({'timestamp': pd.to_datetime(float(ts), unit='s', utc=True),'source_file':source,'packet_index':i,'protocol':'ERR','src_ip':'','dst_ip':'','src_port':None,'dst_port':None,'payload_len':0,'payload_hash':'','payload_hex_head':'','payload_bytes':b'', 'error':str(e)})
    return pd.DataFrame(rows)
