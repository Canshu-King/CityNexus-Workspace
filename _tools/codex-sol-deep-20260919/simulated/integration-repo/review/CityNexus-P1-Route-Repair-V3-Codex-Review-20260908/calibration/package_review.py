"""Create a reproducible CityNexus renderer review package.

Unlike the historical flattened review ZIP, this packager preserves the real
repository layout so the bundled static tests can be rerun from the package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def copy_file(repo: Path, stage: Path, rel: str) -> None:
    src = repo / rel
    if not src.exists():
        raise FileNotFoundError(src)
    dst = stage / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="CityNexus repository root")
    ap.add_argument("--output", required=True, help="Output review ZIP")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    output = Path(args.output).resolve()

    renderer_files = [
        "visio-renderer/README.md",
        "visio-renderer/TOOLCHAIN-BASELINE.md",
        "visio-renderer/render-config.yaml",
        "visio-renderer/native-master-map.json",
        "visio-renderer/phase1-routing.yaml",
        "visio-renderer/build_calibrations.py",
        "visio-renderer/render_core.py",
        "visio-renderer/style_adapter.py",
        "visio-renderer/class_adapter.py",
        "visio-renderer/presentation.py",
        "visio-renderer/routing_geometry.py",
    ]
    calibration_files = [
        "visio-renderer/calibration/build_c4.py",
        "visio-renderer/calibration/validate_c4.py",
        "visio-renderer/calibration/build_c4_1.py",
        "visio-renderer/calibration/validate_c4_1.py",
        "visio-renderer/calibration/C4.1-CODEX-EXECUTION.md",
        "visio-renderer/calibration/build_c4_1a.py",
        "visio-renderer/calibration/validate_c4_1a.py",
        "visio-renderer/calibration/C4.1A-CODEX-EXECUTION.md",
        "visio-renderer/calibration/build_c4_1b.py",
        "visio-renderer/calibration/validate_c4_1b.py",
        "visio-renderer/calibration/C4.1B-CODEX-EXECUTION.md",
        "visio-renderer/calibration/build_c4_1c.py",
        "visio-renderer/calibration/validate_c4_1c.py",
        "visio-renderer/calibration/C4.1C-CODEX-EXECUTION.md",
        "visio-renderer/calibration/build_c4_1d.py",
        "visio-renderer/calibration/validate_c4_1d.py",
        "visio-renderer/calibration/C4.1D-CODEX-EXECUTION.md",
        "visio-renderer/calibration/build_c4_fallback.py",
        "visio-renderer/calibration/validate_c4_fallback.py",
        "visio-renderer/calibration/audit_c4_fallback_openxml.py",
        "visio-renderer/calibration/C4-FALLBACK-CODEX-EXECUTION.md",
        "visio-renderer/calibration/c4-extend-calibration-spec.yaml",
        "visio-renderer/calibration/build_c4_extend.py",
        "visio-renderer/calibration/validate_c4_extend.py",
        "visio-renderer/calibration/C4-EXTEND-CODEX-EXECUTION.md",
        "visio-renderer/calibration/c4-extend-calibration-spec-v0.1.1.yaml",
        "visio-renderer/calibration/build_c4_extend_1.py",
        "visio-renderer/calibration/validate_c4_extend_1.py",
        "visio-renderer/calibration/C4-EXTEND-1-CODEX-EXECUTION.md",
        "visio-renderer/calibration/build_c2_2.py",
        "visio-renderer/calibration/validate_c1.py",
        "visio-renderer/calibration/validate_c2_2.py",
        "visio-renderer/calibration/build_c3.py",
        "visio-renderer/calibration/validate_c3.py",
        "visio-renderer/calibration/c3-presentation-spec.yaml",
        "visio-renderer/calibration/package_review.py",
        "visio-renderer/calibration/c4-routing-calibration-spec.yaml",
        "visio-renderer/calibration/validate_c4_plan.py",
        "visio-renderer/calibration/C4-CODEX-EXECUTION.md",
        "visio-renderer/calibration/update_source_input_hashes.py",
    ]
    spec_files = [
        "visio-spec/style-tokens.yaml",
        "visio-spec/pages/p1_uc_overview.yaml",
    ]

    with tempfile.TemporaryDirectory(prefix="cnx-review-") as tmp:
        stage = Path(tmp) / "CityNexus-Renderer-Review"
        stage.mkdir(parents=True)
        for rel in renderer_files + calibration_files + spec_files:
            if (repo / rel).exists():
                copy_file(repo, stage, rel)

        tests_dir = repo / "visio-renderer/tests"
        if tests_dir.exists():
            shutil.copytree(tests_dir, stage / "visio-renderer/tests", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"))

        out_dir = repo / "visio-renderer/calibration/out"
        if out_dir.exists():
            dst_out = stage / "visio-renderer/calibration/out"
            dst_out.mkdir(parents=True, exist_ok=True)
            for p in out_dir.iterdir():
                if p.is_file() and p.name not in {"manifest.json", "MANIFEST.json"} and not p.name.endswith(".pyc") and not p.name.endswith(".debug-nonauthoritative.svg"):
                    shutil.copy2(p, dst_out / p.name)

        # Prove the staged package layout is itself runnable for static tests.
        renderer_stage = stage / "visio-renderer"
        tr = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=renderer_stage, capture_output=True, text=True)
        report = {"status": "PASS" if tr.returncode == 0 else "FAIL", "stdout": tr.stdout, "stderr": tr.stderr}
        (stage / "REVIEW-PACKAGE-STATIC-TEST.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        # Pytest cache is an execution side effect, never a review artifact.
        shutil.rmtree(renderer_stage / ".pytest_cache", ignore_errors=True)
        if tr.returncode != 0:
            print(tr.stdout)
            print(tr.stderr, file=sys.stderr)
            return tr.returncode

        entries = []
        for p in sorted(stage.rglob("*")):
            if not p.is_file() or p.name == "MANIFEST.json" or "__pycache__" in p.parts or ".pytest_cache" in p.parts or p.suffix == ".pyc" or p.name.endswith(".debug-nonauthoritative.svg"):
                continue
            rel = p.relative_to(stage).as_posix()
            entries.append({"path": rel, "bytes": p.stat().st_size, "sha256": sha256(p)})
        manifest = {
            "format": "CityNexus reproducible renderer review package",
            "layoutPreserved": True,
            "staticTestsInStagedPackage": "PASS",
            "files": entries,
        }
        (stage / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            output.unlink()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(stage.rglob("*")):
                if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts and p.suffix != ".pyc" and not p.name.endswith(".debug-nonauthoritative.svg"):
                    z.write(p, p.relative_to(stage).as_posix())
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
