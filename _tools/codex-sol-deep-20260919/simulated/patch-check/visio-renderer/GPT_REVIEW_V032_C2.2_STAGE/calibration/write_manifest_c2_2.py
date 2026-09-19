"""Create a clean, self-hashing C2.2 review-package manifest."""
from __future__ import annotations
import hashlib
import json
import os
import sys


def main(stage: str) -> int:
    stage = os.path.abspath(stage)
    entries = []
    for root, dirs, files in os.walk(stage):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in sorted(files):
            if name in {"MANIFEST.json", "manifest.json"} or name.endswith(".pyc"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, stage).replace(os.sep, "/")
            data = open(path, "rb").read()
            entries.append({"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest().upper()})
    payload = {
        "release": "CityNexus Visio Renderer v0.3.2 C2.2 Review Package",
        "calibration": {"C1": "FROZEN_PASS", "C2": "FROZEN_PASS", "C3": "BLOCKED", "C4": "BLOCKED"},
        "formalPagesRendered": False,
        "historicalArtifacts": ["C2_Anchored_Class_v2.vsdx (kept outside package; unchanged)"],
        "files": entries,
    }
    with open(os.path.join(stage, "MANIFEST.json"), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(json.dumps({"status": "PASS", "fileCount": len(entries)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
