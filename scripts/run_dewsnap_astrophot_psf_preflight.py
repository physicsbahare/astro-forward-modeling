#!/usr/bin/env python3
"""C6a: exercise AstroPhot's signed empirical-PSF conventions."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
from astropy.io import fits
import torch
import astrophot as ap
from astrophot.models.func.convolution import convolve

ASTROPHOT_VERSION = "0.18.0"
ASTROPHOT_TAG_COMMIT = "b20c98b4acba4b9708938610e61aced60f205620"
TORCH_VERSION = "2.14.0+cpu"
ATOL = 1e-12


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def configuration():
    return {
        "stage": "C6a",
        "astrophot_version": ASTROPHOT_VERSION,
        "astrophot_tag_commit": ASTROPHOT_TAG_COMMIT,
        "torch_version": TORCH_VERSION,
        "modules": ["A", "B"],
        "delta_shape": [201, 201],
        "absolute_identity_tolerance": ATOL,
        "negative_psf_samples_clipped": False,
        "claim": "signed-PSF installation and convention preflight only",
    }


def evaluate(psf):
    started = time.monotonic()
    image = ap.image.PSFImage(data=psf)
    public = image.data.detach().cpu().numpy()
    roundtrip_error = float(np.max(np.abs(public - psf)))
    image.normalize()
    normalized_public = image.data.detach().cpu().numpy()
    delta = torch.zeros((201, 201), dtype=ap.config.DTYPE, device=ap.config.DEVICE)
    delta[100, 100] = 1.0
    rendered_internal = convolve(delta, image._data).detach().cpu().numpy()
    expected_internal = normalized_public.T
    return {
        "input_sum": float(psf.sum()),
        "input_min": float(psf.min()),
        "negative_pixel_count": int(np.count_nonzero(psf < 0)),
        "public_roundtrip_max_abs_error": roundtrip_error,
        "normalized_sum": float(normalized_public.sum()),
        "normalized_min": float(normalized_public.min()),
        "convolution_sum": float(rendered_internal.sum()),
        "convolution_min": float(rendered_internal.min()),
        "internal_transpose_max_abs_error": float(np.max(np.abs(rendered_internal - expected_internal))),
        "untransposed_max_abs_error": float(np.max(np.abs(rendered_internal - normalized_public))),
        "wall_seconds": time.monotonic() - started,
    }, normalized_public, rendered_internal


def run(source, out):
    assert importlib.metadata.version("astrophot") == ASTROPHOT_VERSION
    assert torch.__version__ == TORCH_VERSION
    out.mkdir(parents=True, exist_ok=True)
    cfg = configuration()
    dump(out / "config.json", cfg)
    results = []
    arrays = {}
    for module in cfg["modules"]:
        psf = np.asarray(fits.getdata(source / "inputs" / f"psf_{module}.fits"), dtype=float)
        metrics, normalized, rendered = evaluate(psf)
        metrics["module"] = module
        results.append(metrics)
        arrays[f"psf_{module}_input"] = psf
        arrays[f"psf_{module}_normalized_public"] = normalized
        arrays[f"psf_{module}_delta_convolution_internal"] = rendered
    np.savez_compressed(out / "arrays.npz", **arrays)
    summary = {"config": cfg, "results": results}
    dump(out / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.out), sort_keys=True))


if __name__ == "__main__":
    main()
