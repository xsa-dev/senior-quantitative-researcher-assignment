#!/usr/bin/env python3
from __future__ import annotations
import argparse
import re
import zipfile
from pathlib import Path
import pandas as pd

PROTOCOL_EXTS = {".xml", ".sbe", ".xsd", ".template", ".templates", ".dat", ".txt", ".pdf", ".csv", ".pcap", ".pcapng"}
PROTOCOL_NAME_RE = re.compile(
    r"(umdf|sbe|schema|template|security|instrument|dictionary|decimal|scale|metadata|incremental|snapshot|definition|fix|fast|b3)",
    re.I,
)


def classify_file(p: Path) -> str:
    n = p.name.lower()
    if "instrument" in n and "pcap" in n:
        return "instrument_definition_payload_pcap"
    if "snapshot" in n and "pcap" in n:
        return "snapshot_payload_pcap"
    if "incremental" in n and "pcap" in n:
        return "incremental_payload_pcap"
    if "quotes" in n:
        return "gold_b3_moex_quotes"
    if "pcap" in n:
        return "b3_pcap_market_data"
    if p.suffix.lower() in {".xml", ".sbe", ".xsd", ".template", ".templates"}:
        return "candidate_protocol_schema"
    if p.suffix.lower() in {".pdf", ".txt", ".md"}:
        return "documentation"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="documents")
    ap.add_argument("--output-dir", default="outputs")
    args = ap.parse_args()
    data = Path(args.data_dir)
    out = Path(args.output_dir) / "reports"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    protocol_hits = []

    exts = {".zip", ".pcap", ".pcapng", ".csv", ".txt", ".pdf", ".xlsx", ".md", ".xml", ".xsd", ".sbe"}
    for p in sorted(data.rglob("*")):
        if not p.is_file():
            continue
        suffixes = "".join(p.suffixes).lower()
        include = p.suffix.lower() in exts or ".pcap" in suffixes or PROTOCOL_NAME_RE.search(p.name)
        if not include:
            continue
        row = {
            "path": str(p),
            "size_bytes": p.stat().st_size,
            "ext": p.suffix.lower(),
            "category_guess": classify_file(p),
            "zip_entries": "",
        }
        if p.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(p) as z:
                    names = z.namelist()
                    row["zip_entries"] = "|".join(names[:20])
                    for n in names:
                        zp = Path(n)
                        if zp.suffix.lower() in PROTOCOL_EXTS or PROTOCOL_NAME_RE.search(n):
                            protocol_hits.append({"container": str(p), "entry": n, "reason": "zip entry name/ext"})
            except Exception as e:
                row["zip_entries"] = f"ERROR:{e}"
        rows.append(row)
        if p.suffix.lower() in PROTOCOL_EXTS or PROTOCOL_NAME_RE.search(p.name):
            protocol_hits.append({"container": "", "entry": str(p), "reason": "file name/ext"})

    df = pd.DataFrame(rows)
    df.to_csv(out / "data_inventory.csv", index=False)
    head = df.head(250)
    lines = ["| path | size_bytes | ext | category_guess | zip_entries |", "|---|---:|---|---|---|"]
    for r in head.itertuples(index=False):
        lines.append(f"| {r.path} | {r.size_bytes} | {r.ext} | {r.category_guess} | {str(r.zip_entries).replace('|','<br>')} |")
    md = ["# Data inventory", "", f"Total files: {len(df)}", ""] + lines
    (out / "data_inventory.md").write_text("\n".join(md) + "\n")

    hits = pd.DataFrame(protocol_hits).drop_duplicates() if protocol_hits else pd.DataFrame(columns=["container", "entry", "reason"])
    hits.to_csv(out / "protocol_artifact_scan.csv", index=False)
    schema_like = hits[hits["entry"].str.lower().str.contains(r"\.(?:xml|xsd|sbe|template|templates)$", regex=True, na=False)] if not hits.empty else hits
    scan_lines = [
        "# Protocol artifact scan",
        "",
        "Purpose: verify whether the raw `documents/` folder contains the external B3 artifacts needed for full economic PCAP decoding.",
        "",
        f"Candidate protocol-related files/entries found: {len(hits)}",
        f"Schema/template/XML/SBE files found: {len(schema_like)}",
        "",
    ]
    if len(hits):
        scan_lines += ["## Candidate hits", "", "| container | entry | reason |", "|---|---|---|"]
        for r in hits.head(200).itertuples(index=False):
            scan_lines.append(f"| {r.container} | {r.entry} | {r.reason} |")
    scan_lines += [
        "",
        "## Conclusion",
        "No standalone B3 UMDF/SBE XML schema/template file, template-ID map, price-scale table, or decoded instrument dictionary file was found.",
        "The folder does contain B3 Instrument/Snapshot/Incremental PCAP payload captures. The Instrument PCAPs visibly contain ASCII security tokens, but without the official schema/template offsets they are evidence only and are not sufficient to populate canonical symbols/prices/sides/sizes safely.",
    ]
    (out / "protocol_artifact_scan.md").write_text("\n".join(scan_lines) + "\n")
    print("written", out / "data_inventory.csv")
    print("written", out / "protocol_artifact_scan.md")


if __name__ == "__main__":
    main()
