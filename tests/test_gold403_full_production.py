import ast
from pathlib import Path


def test_production_exposes_exact_case_reruns_without_source_wide_reruns():
    source = Path("scripts/run_gold403_full_production.py").read_text()
    ast.parse(source)
    assert 'parser.add_argument("--force-case"' in source
    assert 'force_cases = set(args.force_case)' in source
