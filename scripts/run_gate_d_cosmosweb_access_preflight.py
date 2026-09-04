#!/usr/bin/env python3
"""Gate D0: metadata-only COSMOS-Web DR1 product access/provenance preflight."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.error
import urllib.request

BASE = "https://cosmos2025.iap.fr/data/nircam/extensions"
PRODUCTS = {
    ext: f"{BASE}/mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v1.0_{ext}.fits.gz"
    for ext in ("sci", "err", "wht")
}
USER_AGENT = "astro-forward-modeling-gate-d0/0.1"


def configuration() -> dict:
    return {
        "stage": "Gate D0 COSMOS-Web DR1 access/provenance preflight",
        "survey": "COSMOS-Web DR1",
        "instrument": "JWST/NIRCam",
        "filter": "F444W",
        "pixel_scale_mas": 30,
        "tile": "A1",
        "products": PRODUCTS,
        "request_method": "HEAD",
        "tile_downloaded": False,
        "injection_performed": False,
        "claim": "metadata-only real-product access/provenance preflight; does not close Gate D",
    }


def probe(url: str, timeout: float = 30.0) -> dict:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            headers = response.headers
            return {
                "url": url,
                "ok": 200 <= response.status < 400,
                "status": int(response.status),
                "final_url": response.geturl(),
                "content_type": headers.get("Content-Type"),
                "content_length": headers.get("Content-Length"),
                "etag": headers.get("ETag"),
                "last_modified": headers.get("Last-Modified"),
                "accept_ranges": headers.get("Accept-Ranges"),
            }
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "ok": False,
            "status": int(exc.code),
            "error": f"HTTPError: {exc}",
        }
    except Exception as exc:
        return {
            "url": url,
            "ok": False,
            "status": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def run(out: Path, timeout: float = 30.0) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    cfg = configuration()
    results = {name: probe(url, timeout=timeout) for name, url in PRODUCTS.items()}
    summary = {
        "config": cfg,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "all_reachable": all(row["ok"] for row in results.values()),
    }
    (out / "config.json").write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    summary = run(args.out, timeout=args.timeout)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not summary["all_reachable"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
