"""Regression checks for the intentionally small active GitHub Actions surface."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

ACTIVE_WORKFLOWS = {
    "verification.yml",
    "passive-spiral-p1.yml",
    "passive-spiral-p2-real-context.yml",
    "passive-spiral-p3-phase-null.yml",
    "passive-spiral-p4-mask-control.yml",
    "passive-spiral-p5-robust-loss.yml",
}


def test_active_workflow_surface_is_small_and_documented():
    present = {p.name for p in WORKFLOWS.glob("*.yml")}
    assert present == ACTIVE_WORKFLOWS
    assert (WORKFLOWS / "README.md").exists()


def test_verification_runs_on_main_and_keeps_real_tests():
    content = (WORKFLOWS / "verification.yml").read_text()
    assert "  push:\n    branches:\n      - main" in content
    assert "  pull_request:" in content
    assert "workflow_dispatch:" in content
    assert 'python-version: ["3.11", "3.12"]' in content
    assert 'run: python -m pip install -e ".[test]"' in content
    assert "run: pytest -q" in content
    assert "verification-v0.1" not in content
    assert "pull_request.number == 5" not in content


def test_retained_passive_spiral_workflows_target_main():
    for name in sorted(ACTIVE_WORKFLOWS - {"verification.yml"}):
        content = (WORKFLOWS / name).read_text()
        assert "verification-v0.1" not in content
        assert "main" in content
        assert "workflow_dispatch:" in content


def test_semantic_workflow_validator_is_pinned():
    content = (WORKFLOWS / "verification.yml").read_text()
    step = content.split(
        "- name: Validate workflow expressions with pinned actionlint", 1
    )[1].split("- name:", 1)[0]
    assert "matrix.python-version == '3.12'" in step
    assert (
        "releases/download/v1.7.12/"
        "actionlint_1.7.12_linux_amd64.tar.gz"
    ) in step
    assert (
        "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"
        in step
    )
    assert "sha256sum --check -" in step
    assert 'actionlint" -shellcheck= -pyflakes= .github/workflows/*.yml' in step
