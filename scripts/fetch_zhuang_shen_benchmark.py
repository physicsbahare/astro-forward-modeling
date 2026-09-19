#!/usr/bin/env python3
"""Fetch an immutable subset of the Zhuang & Shen benchmark products.

The upstream repository is pinned to a specific Git commit. Each downloaded file
is checked against the Git blob SHA recorded from that commit, then a SHA-256
manifest is written locally. Third-party benchmark data remain outside git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

UPSTREAM_REPO = "mingyangzhuang/JWST-NIRCam-Data-Product"
UPSTREAM_COMMIT = "0a55283e973e2dc055ab807e29a04d89733fee48"
RAW_ROOT = "https://raw.githubusercontent.com/" f"{UPSTREAM_REPO}/{UPSTREAM_COMMIT}"

FILES = {
    "info": {
        "path": "mock_AGN_results/Info.ipac",
        "git_blob_sha": "2d638aa347968c1560e3da0373d14506170acbd6",
    },
    "input": {
        "path": "mock_AGN_results/mock_AGN_input_values.ipac",
        "git_blob_sha": "a213e127759b71b42df929d604a1d96bb5ac9659",
    },
    "f115w_fiducial": {
        "path": "mock_AGN_results/mock_AGN_results_F115W_fiducial_PSF.ipac",
        "git_blob_sha": "761d7d3c379cb95ca0abd8eb809e60d1a1f4375d",
    },
    "f115w_broader": {
        "path": "mock_AGN_results/mock_AGN_results_F115W_broader_PSF.ipac",
        "git_blob_sha": "f9d9011eb1d751f5220fafab6ad1adddbeb04322",
    },
    "f115w_narrower": {
        "path": "mock_AGN_results/mock_AGN_results_F115W_narrower_PSF.ipac",
        "git_blob_sha": "6f183825eb56a2afb99c750ce4cd8469941390c1",
    },
    "f115w_center_free": {
        "path": "mock_AGN_results/mock_AGN_results_F115W_fiducial_PSF_center_not_tied.ipac",
        "git_blob_sha": "2d25e9dfc03a61e98786fc67607cbadf014081ab",
    },
    "f150w_fiducial": {
        "path": "mock_AGN_results/mock_AGN_results_F150W_fiducial_PSF.ipac",
        "git_blob_sha": "dffb475548618f8db8f67e5df678d40f00034964",
    },
    "f150w_broader": {
        "path": "mock_AGN_results/mock_AGN_results_F150W_broader_PSF.ipac",
        "git_blob_sha": "c9cc22c2566295d65a27c8b86190225f48999a69",
    },
    "f150w_narrower": {
        "path": "mock_AGN_results/mock_AGN_results_F150W_narrower_PSF.ipac",
        "git_blob_sha": "06bb790e75f48a085bacedec7cd28afce22596e5",
    },
    "f150w_center_free": {
        "path": "mock_AGN_results/mock_AGN_results_F150W_fiducial_PSF_center_not_tied.ipac",
        "git_blob_sha": "a7f7929509cd777805fcdf8a23a4f2c1cf1c3324",
    },
}

DEFAULT_KEYS = tuple(FILES)


def git_blob_sha1(data: bytes) -> str:
    """Return the SHA-1 used by Git for a blob with exactly these bytes."""

    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def fetch_one(key: str, output_root: Path) -> dict[str, object]:
    spec = FILES[key]
    relpath = Path(str(spec["path"]))
    url = f"{RAW_ROOT}/{relpath.as_posix()}"
    target = output_root / relpath
    target.parent.mkdir(parents=True, exist_ok=True)

    with urlopen(url, timeout=120) as response:
        data = response.read()

    observed_blob = git_blob_sha1(data)
    expected_blob = str(spec["git_blob_sha"])
    if observed_blob != expected_blob:
        raise RuntimeError(
            f"Git blob mismatch for {relpath}: expected {expected_blob}, "
            f"observed {observed_blob}. Refusing to use the file."
        )

    target.write_bytes(data)
    return {
        "key": key,
        "path": relpath.as_posix(),
        "bytes": len(data),
        "git_blob_sha1": observed_blob,
        "sha256": hashlib.sha256(data).hexdigest(),
        "url": url,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("external_data/zhuang_shen_2024"),
        help="Local benchmark-data root (ignored by git).",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        choices=sorted(FILES),
        default=list(DEFAULT_KEYS),
        help="Named files to retrieve.",
    )
    args = parser.parse_args()

    records = [fetch_one(key, args.output) for key in args.keys]
    manifest = {
        "upstream_repository": UPSTREAM_REPO,
        "upstream_commit": UPSTREAM_COMMIT,
        "files": records,
    }
    manifest_path = args.output / "manifest.sha256.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(f"Verified {len(records)} files from immutable upstream commit {UPSTREAM_COMMIT}.")
    print(f"Manifest: {manifest_path}")
    for record in records:
        print(f"{record['path']}: {record['bytes']} bytes, sha256={record['sha256']}")


if __name__ == "__main__":
    main()
