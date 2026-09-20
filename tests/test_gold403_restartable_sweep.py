import csv
import importlib.util
import json
from pathlib import Path

import pytest

REQUIRED = ("id", "status", "metric")


def _load_module():
    path = Path("scripts/gold403_restartable_sweep.py")
    spec = importlib.util.spec_from_file_location("gold403_restartable", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checkpoint_write_is_readable_and_replaces_prior_rows(tmp_path):
    """A partial sweep receipt is atomically materialized as a valid CSV."""
    module = _load_module()
    receipt = tmp_path / "checkpoint.csv"
    module.write_checkpoint_rows(
        receipt,
        [
            {"id": 11, "status": "OK", "metric": 1.5},
            {"id": 12, "status": "ERROR", "metric": ""},
        ],
        REQUIRED,
    )

    assert module.load_valid_checkpoint(receipt, {11, 12, 13}, REQUIRED) == [
        {"id": "11", "status": "OK", "metric": "1.5"},
        {"id": "12", "status": "ERROR", "metric": ""},
    ]
    assert not list(tmp_path.glob(".checkpoint.csv.*.tmp"))


def test_checkpoint_rejects_duplicate_ids_before_resume(tmp_path):
    """Duplicate object rows must never be silently skipped or overwritten."""
    module = _load_module()
    receipt = tmp_path / "checkpoint.csv"
    with receipt.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=REQUIRED)
        writer.writeheader()
        writer.writerows(
            [
                {"id": 11, "status": "OK", "metric": 1.5},
                {"id": 11, "status": "ERROR", "metric": ""},
            ]
        )

    with pytest.raises(module.CheckpointValidationError, match="duplicate"):
        module.load_valid_checkpoint(receipt, {11}, REQUIRED)


def test_restartable_runner_skips_checkpointed_error_and_forces_one_id(tmp_path):
    """Resume retains failures, while an explicit force replaces only one row."""
    module = _load_module()
    receipt = tmp_path / "checkpoint.csv"
    log = tmp_path / "run.log"
    provenance = tmp_path / "provenance.json"
    calls = []

    def runner(object_id):
        calls.append(object_id)
        if object_id == 12:
            raise RuntimeError("context invalid")
        return {"id": object_id, "status": "OK", "metric": object_id / 10}

    first = module.run_restartable_sweep(
        [11, 12, 13],
        output_csv=receipt,
        fieldnames=("id", "status", "metric", "error"),
        object_runner=runner,
        provenance_path=provenance,
        log_path=log,
        config={"target_filter": "F444W", "pso_repeats": 2},
        software_versions={"python": "test"},
    )

    assert calls == [11, 12, 13]
    assert [row["status"] for row in first] == ["OK", "ERROR", "OK"]
    assert json.loads(provenance.read_text())["config"]["target_filter"] == "F444W"

    calls.clear()
    second = module.run_restartable_sweep(
        [11, 12, 13],
        output_csv=receipt,
        fieldnames=("id", "status", "metric", "error"),
        object_runner=runner,
        provenance_path=provenance,
        log_path=log,
        config={"target_filter": "F444W", "pso_repeats": 2},
        software_versions={"python": "test"},
        force_ids={12},
    )

    assert calls == [12]
    assert [row["id"] for row in second] == ["11", "12", "13"]
    assert [row["status"] for row in second] == ["OK", "ERROR", "OK"]
    assert "completed=3 skipped=2 forced=1" in log.read_text()


def test_restart_refuses_to_mix_a_checkpoint_with_different_configuration(tmp_path):
    """Changing scientific configuration requires a distinct receipt, not a skip."""
    module = _load_module()
    receipt = tmp_path / "checkpoint.csv"
    provenance = tmp_path / "provenance.json"
    log = tmp_path / "run.log"

    def runner(object_id):
        return {"id": object_id, "status": "OK", "metric": 1.0}

    module.run_restartable_sweep(
        [11],
        output_csv=receipt,
        fieldnames=("id", "status", "metric", "error"),
        object_runner=runner,
        provenance_path=provenance,
        log_path=log,
        config={"target_filter": "F444W"},
        software_versions={"python": "test"},
    )

    with pytest.raises(module.CheckpointValidationError, match="configuration"):
        module.run_restartable_sweep(
            [11],
            output_csv=receipt,
            fieldnames=("id", "status", "metric", "error"),
            object_runner=runner,
            provenance_path=provenance,
            log_path=log,
            config={"target_filter": "F277W"},
            software_versions={"python": "test"},
        )


def test_restartable_runner_can_stop_after_only_forced_case(tmp_path):
    """A diagnostic rerun must not advance later uncheckpointed production IDs."""
    module = _load_module()
    receipt = tmp_path / "checkpoint.csv"
    log = tmp_path / "run.log"
    provenance = tmp_path / "provenance.json"
    fields = ("id", "status", "metric", "error")
    module.write_checkpoint_rows(receipt, [{"id": 11, "status": "OK", "metric": 1.1, "error": ""}], fields)
    provenance.write_text(json.dumps({"object_ids": [11, 12, 13], "config": {"target_filter": "F444W"}}))
    calls = []

    def runner(object_id):
        calls.append(object_id)
        return {"id": object_id, "status": "ERROR", "metric": "", "error": "diagnostic"}

    rows = module.run_restartable_sweep(
        [11, 12, 13], output_csv=receipt, fieldnames=fields, object_runner=runner,
        provenance_path=provenance, log_path=log, config={"target_filter": "F444W"},
        software_versions={"python": "test"}, force_ids={12}, stop_after_forced=True,
    )

    assert calls == [12]
    assert [int(row["id"]) for row in rows] == [11, 12]
    assert "controlled_stop_after_forced" in log.read_text()
