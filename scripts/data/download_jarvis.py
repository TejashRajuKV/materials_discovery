"""Download a JARVIS dataset to ml/data/raw/ with provenance metadata."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jarvis.db.figshare import data

RAW_DIR = Path(__file__).resolve().parents[2] / "ml" / "data" / "raw"
METADATA_DIR = Path(__file__).resolve().parents[2] / "ml" / "data" / "metadata"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", help="JARVIS dataset name, e.g. dft_3d")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    retrieved_at = datetime.now(timezone.utc).isoformat()
    print(f"Downloading '{args.dataset}' from JARVIS (figshare)...", flush=True)
    records = data(args.dataset)
    print(f"Retrieved {len(records)} records at {retrieved_at}", flush=True)

    raw_path = RAW_DIR / f"{args.dataset}.json"
    with raw_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle)
    print(f"Wrote {raw_path} ({raw_path.stat().st_size / 1e6:.1f} MB)", flush=True)

    fields = sorted(records[0].keys()) if records else []
    populated = {
        field: sum(1 for r in records if r.get(field) not in (None, "", [], {}))
        for field in fields
    }

    metadata = {
        "source": "JARVIS (NIST) via jarvis-tools figshare",
        "collection": args.dataset,
        "retrieved_at": retrieved_at,
        "number_of_records": len(records),
        "raw_file": str(raw_path.relative_to(RAW_DIR.parents[2])),
        "fields": fields,
        "field_populated_counts": populated,
        "processing_version": None,
    }
    metadata_path = METADATA_DIR / f"{args.dataset}_source.json"
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
    print(f"Wrote {metadata_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
