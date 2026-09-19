import ast
from pathlib import Path


SCRIPT = Path("scripts/gold403_validation_notebook_cells.py")


def test_gold403_validation_helper_is_valid_python():
    source = SCRIPT.read_text(encoding="utf-8")
    ast.parse(source)


def test_gold403_validation_helper_contains_required_stages():
    source = SCRIPT.read_text(encoding="utf-8")
    required = [
        "make_exact_lenstronomy_single_truth",
        "run_perturbed_lenstronomy_test",
        "make_exact_lenstronomy_bd_truth",
        "run_exact_bd_validation",
        "run_native_clean_baseline",
        "run_clean_identifiability_sweep",
        "KNOWN_DIAGNOSTICS",
    ]
    for name in required:
        assert name in source
