"""Native GitHub condition snapshots: routing must never alter science steps."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
DRAFT="!(github.event_name == 'pull_request' && github.event.pull_request.number == 5 && github.event.pull_request.draft)"
BOOTSTRAP="!(github.event_name == 'push' && github.ref == 'refs/heads/verification-v0.1' && github.event.before == '88f3fb646a0b89e6cb9b8b8ee1aacae377edca56' && contains(github.event.head_commit.message, '[C5e isolated]'))"


def test_legacy_job_guards_and_ready_for_review_event():
    record=json.loads((ROOT/'benchmarks/zhuang_shen_2024/ci_routing_20260903.json').read_text())
    assert len(record['workflows'])==32
    for entry in record['workflows']:
        path=entry['path']; content=(ROOT/path).read_text()
        assert 'types: [opened, synchronize, reopened, ready_for_review]' in content
        expected=DRAFT if path.endswith('/verification.yml') else DRAFT+' && '+BOOTSTRAP
        jobs=content.split('\njobs:\n',1)[1]
        n_jobs=len(re.findall(r'^  [A-Za-z0-9_-]+:\n',jobs,re.M))
        assert jobs.count('    if: ${{ '+expected+' }}')==n_jobs
        assert 'continue-on-error: true' not in jobs


def test_full_regression_push_is_not_skipped():
    content=(ROOT/'.github/workflows/verification.yml').read_text()
    assert '  push:\n    branches:\n      - verification-v0.1' in content
    assert '[C5e isolated]' not in content
    assert 'run: pytest -q' in content
    assert 'python-version: ["3.11", "3.12"]' in content


def test_selected_experiment_has_no_legacy_skip_guard():
    content=(ROOT/'.github/workflows/gate-c-agn-empirical-psf-phase.yml').read_text()
    assert '  pull_request:' not in content
    assert '    if:' not in content.split('    steps:',1)[0]
    assert '[C5e isolated]' not in content
    assert 'cancel-in-progress: false' in content
    assert 'matrix:\n        module: [A, B]' in content
    assert 'run-id: 33717899427' in content
    assert 'test_agn_empirical_psf_phase.py' in content


def test_gate_b_push_paths_preserve_code_dependency_coverage():
    for name in ['gate-b-core.yml','gate-b-jwst-stpsf.yml']:
        trigger=(ROOT/'.github/workflows'/name).read_text().split('  pull_request:',1)[0]
        for path in ['crosscode/**','verification/**','requirements-crosscode-*.txt','pyproject.toml',
                     '.github/workflows/'+name]:
            assert "      - '"+path+"'" in trigger


def test_calibration_cache_is_resolved_at_runtime_not_job_context():
    content=(ROOT/'.github/workflows/gate-b-jwst-pipeline.yml').read_text()
    job_env=content.split('    env:',1)[1].split('    steps:',1)[0]
    assert 'runner.temp' not in job_env
    assert 'CRDS_PATH:' not in job_env
    assert 'CRDS_CONTEXT: "jwst_1584.pmap"' in job_env
    setup=content.split('- name: Resolve calibration cache on the runner',1)[1].split('- name:',1)[0]
    assert "printf 'CRDS_PATH=%s/crds-cache\\n'" in setup
    assert '"$RUNNER_TEMP" >> "$GITHUB_ENV"' in setup
    assert content.index('Resolve calibration cache') < content.index('Install pinned JWST pipeline')


def test_semantic_workflow_validator_is_pinned_and_does_not_replace_tests():
    content=(ROOT/'.github/workflows/verification.yml').read_text()
    step=content.split('- name: Validate workflow expressions with pinned actionlint',1)[1].split('- name:',1)[0]
    assert "if: matrix.python-version == '3.12'" in step
    assert 'releases/download/v1.7.12/actionlint_1.7.12_linux_amd64.tar.gz' in step
    assert '8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8' in step
    assert 'sha256sum --check -' in step
    assert 'actionlint" -shellcheck= -pyflakes= .github/workflows/*.yml' in step
    assert 'run: pytest -q' in content
