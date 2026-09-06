from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "audit_gate_d_cosmosweb_embedded_asdf.py"
)

spec = importlib.util.spec_from_file_location("gate_d_embedded_asdf_audit", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_yaml_prefix_stops_before_binary_blocks() -> None:
    payload = b"#ASDF 1.0.0\n---\nmeta:\n  pixfrac: 1.0\n...\nBINARY\x00\x01"
    assert module._yaml_prefix(payload) == b"#ASDF 1.0.0\n---\nmeta:\n  pixfrac: 1.0\n...\n"


def test_final_kernel_requires_resample_or_drizzle_context() -> None:
    tree = {
        "meta": {
            "resample": {"kernel": "square", "pixfrac": "1.0"},
            "other": {"kernel": "lanczos"},
        }
    }
    matches = module._collect_matches(tree)
    candidates = module._final_kernel_candidates(matches)
    assert len(candidates) == 1
    assert candidates[0]["path"] == "meta.resample.kernel"
    assert "square" in candidates[0]["value_preview"]


def test_generic_kernel_is_not_promoted() -> None:
    tree = {"meta": {"wcs": {"kernel": "spline"}}}
    matches = module._collect_matches(tree)
    assert module._final_kernel_candidates(matches) == []
