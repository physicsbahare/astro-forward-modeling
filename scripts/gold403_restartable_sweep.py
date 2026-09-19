"""Crash-safe persistence utilities for GOLD403 notebook-integrated sweeps.

This module intentionally contains no renderer or fitter.  It protects the
scientific records produced by the validated Lenstronomy/Galight helpers.
"""

from __future__ import annotations

import csv
import json
import os
import platform
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence


class CheckpointValidationError(ValueError):
    """Raised when a checkpoint is unsafe to use for a resumed run."""


def write_checkpoint_rows(
    path: str | Path,
    rows: Iterable[Mapping[str, object]],
    fieldnames: Sequence[str],
) -> None:
    """Atomically replace a CSV receipt after validating its schema locally."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    fields = list(fieldnames)

    for row in rows:
        missing = [name for name in fields if name not in row]
        if missing:
            raise CheckpointValidationError(
                "row is missing required columns: " + ", ".join(missing)
            )

    with tempfile.NamedTemporaryFile(
        mode="w",
        newline="",
        encoding="utf-8",
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())

    try:
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_valid_checkpoint(
    path: str | Path,
    expected_ids: set[int],
    required_columns: Sequence[str],
) -> list[dict[str, str]]:
    """Return resume-safe rows or reject malformed, unknown, duplicate records."""
    receipt = Path(path)
    if not receipt.exists():
        return []

    with receipt.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        missing = [name for name in required_columns if name not in columns]
        if missing:
            raise CheckpointValidationError(
                "checkpoint is missing required columns: " + ", ".join(missing)
            )
        rows = list(reader)

    seen: set[int] = set()
    for row in rows:
        if not row.get("id", "").strip():
            raise CheckpointValidationError("checkpoint has an empty id")
        try:
            object_id = int(row["id"])
        except ValueError as exc:
            raise CheckpointValidationError(
                f"checkpoint has non-integer id: {row['id']!r}"
            ) from exc
        if object_id not in expected_ids:
            raise CheckpointValidationError(
                f"checkpoint contains unexpected id: {object_id}"
            )
        if object_id in seen:
            raise CheckpointValidationError(
                f"checkpoint contains duplicate id: {object_id}"
            )
        if not row.get("status", "").strip():
            raise CheckpointValidationError(
                f"checkpoint has empty status for id: {object_id}"
            )
        seen.add(object_id)

    return rows


def _atomic_write_json(path: str | Path, payload: Mapping[str, object]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _append_log(path: str | Path, message: str) -> None:
    log = Path(path)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as stream:
        stream.write(message + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _normalized_record(
    record: Mapping[str, object], fieldnames: Sequence[str]
) -> dict[str, object]:
    missing = [name for name in ("id", "status") if name not in record]
    if missing:
        raise CheckpointValidationError(
            "object runner result is missing required columns: " + ", ".join(missing)
        )
    return {name: record.get(name, "") for name in fieldnames}


def run_restartable_sweep(
    object_ids: Sequence[int],
    *,
    output_csv: str | Path,
    fieldnames: Sequence[str],
    object_runner: Callable[[int], Mapping[str, object]],
    provenance_path: str | Path,
    log_path: str | Path,
    config: Mapping[str, object],
    software_versions: Mapping[str, object],
    force_ids: set[int] | None = None,
) -> list[dict[str, str]]:
    """Run one object at a time, atomically saving a complete receipt each time.

    Any valid pre-existing row, including an `ERROR` row, is skipped unless its
    object ID is explicitly in `force_ids`.  A forced result replaces only its
    prior row, keeping the receipt at one row per requested object.
    """
    ordered_ids = [int(object_id) for object_id in object_ids]
    if len(set(ordered_ids)) != len(ordered_ids):
        raise CheckpointValidationError("requested object IDs contain duplicates")
    if not ordered_ids:
        raise CheckpointValidationError("requested object IDs are empty")
    if "id" not in fieldnames or "status" not in fieldnames:
        raise CheckpointValidationError("fieldnames must include id and status")

    expected_ids = set(ordered_ids)
    forced = {int(object_id) for object_id in (force_ids or set())}
    unknown_forced = forced - expected_ids
    if unknown_forced:
        raise CheckpointValidationError(
            "force_ids are not part of this run: " + ", ".join(map(str, sorted(unknown_forced)))
        )

    existing = load_valid_checkpoint(output_csv, expected_ids, fieldnames)
    existing_provenance = Path(provenance_path)
    if existing_provenance.exists():
        try:
            previous = json.loads(existing_provenance.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CheckpointValidationError("existing provenance is malformed") from exc
        if previous.get("config") != dict(config):
            raise CheckpointValidationError(
                "existing checkpoint provenance has a different configuration"
            )
        if previous.get("object_ids") != ordered_ids:
            raise CheckpointValidationError(
                "existing checkpoint provenance has a different object-ID selection"
            )
    records = {int(row["id"]): dict(row) for row in existing}
    _atomic_write_json(
        provenance_path,
        {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "object_ids": ordered_ids,
            "force_ids": sorted(forced),
            "config": dict(config),
            "software_versions": {
                "python_runtime": platform.python_version(),
                **dict(software_versions),
            },
            "checkpoint_csv": str(Path(output_csv)),
            "run_log": str(Path(log_path)),
        },
    )

    skipped = 0
    rerun = 0
    for object_id in ordered_ids:
        if object_id in records and object_id not in forced:
            skipped += 1
            continue
        if object_id in forced:
            rerun += 1

        try:
            record = dict(object_runner(object_id))
            if int(record.get("id", object_id)) != object_id:
                raise CheckpointValidationError(
                    f"object runner returned ID {record.get('id')!r} for requested ID {object_id}"
                )
            record["id"] = object_id
        except Exception as exc:  # Scientific failures are receipt rows, not drops.
            record = {"id": object_id, "status": "ERROR", "error": repr(exc)}

        records[object_id] = _normalized_record(record, fieldnames)
        rows = [records[oid] for oid in ordered_ids if oid in records]
        write_checkpoint_rows(output_csv, rows, fieldnames)
        _append_log(
            log_path,
            f"{datetime.now(timezone.utc).isoformat()} id={object_id} "
            f"status={records[object_id]['status']} checkpointed={len(rows)}",
        )

    complete = load_valid_checkpoint(output_csv, expected_ids, fieldnames)
    if len(complete) != len(ordered_ids):
        raise CheckpointValidationError(
            f"incomplete checkpoint: found {len(complete)} rows for {len(ordered_ids)} requested IDs"
        )
    _append_log(
        log_path,
        f"{datetime.now(timezone.utc).isoformat()} completed={len(complete)} "
        f"skipped={skipped} forced={rerun}",
    )
    return complete
