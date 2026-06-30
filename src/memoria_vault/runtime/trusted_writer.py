"""Alpha.12 trusted-writer primitives for staging, promotion, and trace scans."""

from __future__ import annotations

import platform
import shutil
import subprocess
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import append_jsonl, iter_jsonl
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.vaultio import split_frontmatter, write_frontmatter_doc

EVENT_DERIVED = "derived"
EVENT_CHECK_FIRED = "check-fired"
EVENT_RESOLVED = "resolved"
SUPPORTED_PROMOTION_CHECKS = frozenset({"memoria-profile"})


def normalize_promotion_checks(
    checks: Iterable[str] | None = None,
    *,
    default: str = "memoria-profile",
) -> list[str]:
    """Return the checks the worker can enforce before marking a Concept checked."""
    raw_checks = [default] if checks is None else list(checks)
    normalized: list[str] = []
    for value in raw_checks:
        if not isinstance(value, str):
            raise ValueError("promotion checks must be strings")
        check = value.strip()
        if not check:
            raise ValueError("promotion checks must be non-empty")
        if check not in normalized:
            normalized.append(check)
    if not normalized:
        raise ValueError("promotion requires at least one check")
    unsupported = sorted(set(normalized) - SUPPORTED_PROMOTION_CHECKS)
    if unsupported:
        raise ValueError(f"unsupported promotion checks: {', '.join(unsupported)}")
    return normalized


def append_journal_event(
    vault: Path,
    event: dict[str, Any],
    *,
    machine: str | None = None,
) -> dict[str, Any]:
    """Append one journal event to ``journal/<machine>.jsonl``."""
    row = dict(event)
    row.setdefault("timestamp", now_iso())
    _append_event(Path(vault), machine, row)
    return row


def commit_writer_changes(
    vault: Path,
    message: str,
    paths: Iterable[str | Path],
    *,
    machine: str | None = None,
) -> str:
    """Commit only the writer-touched bundle paths plus the per-machine journal."""
    vault = Path(vault)
    rels = {_commit_relpath(vault, path) for path in paths}
    rels.add(_rel(vault, _journal_path(vault, machine)))
    selected = sorted(rels)
    _git(vault, ["git", "add", "--", *selected])
    _git(vault, ["git", "commit", "-m", message, "--", *selected])
    commit = _git(vault, ["git", "rev-parse", "HEAD"])
    for rel in selected:
        state.mark_materialized(vault, rel, commit=commit)
    return commit


def observe_pi_edit(
    vault: Path,
    target_path: str,
    prior_sha256: str,
    *,
    inputs: Iterable[str | dict[str, Any]] = (),
    operation: str = "pi-edit",
    run_id: str | None = None,
    machine: str | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Backfill provenance for a direct PI edit and make it ineligible until checked."""
    vault = Path(vault)
    target = _target_path(target_path)
    contract = _load_contract(vault, schemas_dir)
    _bundle_for_target(contract, target)

    path = vault / target
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    frontmatter["check_status"] = "unchecked"
    _validate_concept(contract, target, frontmatter)
    write_frontmatter_doc(path, frontmatter, body, create_parent=True)

    event = {
        "event": EVENT_DERIVED,
        "timestamp": now_iso(),
        "output_id": target,
        "output_sha256": sha256_file(path),
        "inputs": [
            *_input_rows(inputs),
            {"id": target, "sha256": prior_sha256, "role": "prior-head"},
        ],
        "operation": operation,
        "actor": "pi",
    }
    if run_id:
        event["run_id"] = run_id
    _append_event(vault, machine, event)
    return event


def observe_pi_edit_from_head(
    vault: Path,
    target_path: str,
    *,
    operation: str = "pi-edit",
    run_id: str | None = None,
    machine: str | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Backfill a PI edit using the prior git HEAD hash and prior derivation inputs."""
    vault = Path(vault)
    target = _target_path(target_path)
    return observe_pi_edit(
        vault,
        target,
        _head_sha256(vault, target),
        inputs=_latest_derived_inputs(vault, target),
        operation=operation,
        run_id=run_id,
        machine=machine,
        schemas_dir=schemas_dir,
    )


def observe_pi_edits_from_status(
    vault: Path,
    *,
    paths: Iterable[str] | None = None,
    operation: str = "pi-edit",
    machine: str | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Observe direct PI Concept edits from git status and commit the backfill."""
    vault = Path(vault)
    contract = _load_contract(vault, schemas_dir)
    targets = _pi_edit_targets(vault, contract, paths)
    for target in targets:
        _validate_pi_edit_target(vault, contract, target)

    observed = [
        observe_pi_edit_from_head(
            vault,
            target,
            operation=operation,
            machine=machine,
            schemas_dir=schemas_dir,
        )
        for target in targets
    ]
    commit = ""
    if observed:
        commit = commit_writer_changes(vault, "observe PI edits", targets, machine=machine)
    return {"paths": targets, "observed": observed, "commit": commit}


def mark_checked(
    vault: Path,
    target_path: str,
    *,
    check: str = "memoria-profile",
    checks: Iterable[str] | None = None,
    machine: str | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Mark an existing live Concept checked after the worker's checks pass."""
    vault = Path(vault)
    target = _target_path(target_path)
    promotion_checks = normalize_promotion_checks([check] if checks is None else checks)
    contract = _load_contract(vault, schemas_dir)
    _bundle_for_target(contract, target)
    output_path = vault / target
    frontmatter, body = split_frontmatter(output_path.read_text(encoding="utf-8"))
    return _write_checked(
        vault,
        target,
        output_path,
        frontmatter,
        body,
        promotion_checks,
        machine,
        contract,
    )


def stage_concept(
    vault: Path,
    target_path: str,
    content: str,
    *,
    inputs: Iterable[str | dict[str, Any]] = (),
    operation: str = "trusted-writer",
    run_id: str | None = None,
    actor: str = "operation",
    machine: str | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Validate a machine Concept request, stage it unchecked, and journal derivation."""
    vault = Path(vault)
    target = _target_path(target_path)
    contract = _load_contract(vault, schemas_dir)
    _bundle_for_target(contract, target)

    frontmatter, body = split_frontmatter(content)
    frontmatter["check_status"] = "unchecked"
    _validate_concept(contract, target, frontmatter)

    staged_path = _staged_path(vault, target)
    write_frontmatter_doc(staged_path, frontmatter, body, create_parent=True)
    event = {
        "event": EVENT_DERIVED,
        "timestamp": now_iso(),
        "output_id": target,
        "staging_id": _rel(vault, staged_path),
        "output_sha256": sha256_file(staged_path),
        "inputs": _input_rows(inputs),
        "operation": operation,
        "actor": actor,
    }
    if run_id:
        event["run_id"] = run_id
    _append_event(vault, machine, event)
    state.record_file_output(
        vault,
        output_id=target,
        concept_type=str(frontmatter["type"]),
        check_status=str(frontmatter["check_status"]),
        output_sha256=event["output_sha256"],
        staging_id=event["staging_id"],
        payload_text=staged_path.read_text(encoding="utf-8"),
        actor=actor,
        inputs=event["inputs"],
    )
    return event


def promote_checked(
    vault: Path,
    target_path: str,
    *,
    check: str = "memoria-profile",
    checks: Iterable[str] | None = None,
    machine: str | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Promote a staged Concept into its bundle only after it validates as checked."""
    vault = Path(vault)
    target = _target_path(target_path)
    promotion_checks = normalize_promotion_checks([check] if checks is None else checks)
    contract = _load_contract(vault, schemas_dir)
    _bundle_for_target(contract, target)

    staged_path = _staged_path(vault, target)
    if not staged_path.is_file():
        raise FileNotFoundError(staged_path)
    frontmatter, body = split_frontmatter(staged_path.read_text(encoding="utf-8"))
    output_path = vault / target
    event = _write_checked(
        vault,
        target,
        output_path,
        frontmatter,
        body,
        promotion_checks,
        machine,
        contract,
    )
    staged_path.unlink()
    return event


def quarantine_untraced(
    vault: Path,
    paths: Iterable[str],
    *,
    machine: str | None = None,
    reason: str = "foreign-untraced",
) -> list[dict[str, Any]]:
    """Move explicit bundle files whose current hash is not journal-backed."""
    vault = Path(vault)
    known = _known_current_hashes(vault)
    events: list[dict[str, Any]] = []
    for raw_path in paths:
        target = _target_path(raw_path)
        source_path = vault / target
        if not source_path.is_file():
            continue
        original_sha = sha256_file(source_path)
        if known.get(target) == original_sha:
            continue

        frontmatter, body = split_frontmatter(source_path.read_text(encoding="utf-8"))
        frontmatter["check_status"] = "quarantined"
        write_frontmatter_doc(source_path, frontmatter, body, create_parent=True)
        quarantined_sha = sha256_file(source_path)
        quarantine_path = _unique_quarantine_path(vault / ".memoria/quarantine" / target)
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), quarantine_path)
        event = {
            "event": EVENT_CHECK_FIRED,
            "timestamp": now_iso(),
            "check": "trace-integrity",
            "status": "failed",
            "reason": reason,
            "target_id": target,
            "target_sha256": original_sha,
            "quarantined_id": _rel(vault, quarantine_path),
            "output_sha256": quarantined_sha,
        }
        _append_event(vault, machine, event)
        events.append(event)
    return events


def quarantine_untraced_from_status(
    vault: Path,
    *,
    machine: str | None = None,
    reason: str = "foreign-untraced",
    schemas_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Quarantine untraced bundle files reported by git status."""
    vault = Path(vault)
    contract = _load_contract(vault, schemas_dir)
    return quarantine_untraced(
        vault,
        _git_status_paths(vault, contract),
        machine=machine,
        reason=reason,
    )


def rebuild_trace_state(vault: Path) -> dict[str, dict[str, Any]]:
    """Rebuild the latest known output/check state from all per-machine journals."""
    outputs: dict[str, dict[str, Any]] = {}
    for event in _iter_events(Path(vault)):
        if event.get("event") == EVENT_DERIVED:
            output_id = event.get("output_id")
        elif event.get("event") == EVENT_CHECK_FIRED:
            output_id = event.get("target_id")
        else:
            continue
        if isinstance(output_id, str):
            outputs[output_id] = event
    return outputs


def _load_contract(vault: Path, schemas_dir: Path | None) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - packaged deployments install PyYAML.
        raise RuntimeError("trusted writer requires PyYAML to load schemas") from exc

    root = Path(schemas_dir) if schemas_dir else vault / ".memoria/schemas"
    folders = yaml.safe_load((root / "folders.yaml").read_text(encoding="utf-8")) or {}
    types: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "types").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if data.get("type"):
            types[str(data["type"])] = data
    return {"folders": folders, "types": types}


def _target_path(path: str) -> str:
    target = normalize_path(path)
    if not target.endswith(".md"):
        raise ValueError(f"Concept path must be markdown: {path!r}")
    if target.startswith(".memoria/"):
        raise ValueError(f"Concept path must be in a bundle: {path!r}")
    return target


def _bundle_for_target(contract: dict[str, Any], target: str) -> str:
    for root in contract["folders"].get("bundle_roots") or ():
        root = str(root).strip("/")
        if target == root or target.startswith(root + "/"):
            return root
    raise ValueError(f"target is outside bundle roots: {target}")


def _is_bundle_target(contract: dict[str, Any], target: str) -> bool:
    try:
        _bundle_for_target(contract, target)
    except ValueError:
        return False
    return True


def _pi_edit_targets(
    vault: Path,
    contract: dict[str, Any],
    paths: Iterable[str] | None,
) -> list[str]:
    known = _known_current_hashes(vault)
    raw_paths = list(paths) if paths is not None else _git_status_paths(vault, contract)
    targets: list[str] = []
    for raw_path in raw_paths:
        try:
            target = _target_path(raw_path)
        except ValueError:
            continue
        path = vault / target
        if not path.is_file() or not _is_bundle_target(contract, target):
            continue
        if known.get(target) == sha256_file(path):
            continue
        targets.append(target)
    return sorted(set(targets))


def _git_status_paths(vault: Path, contract: dict[str, Any]) -> list[str]:
    roots = [str(root).strip("/") for root in contract["folders"].get("bundle_roots") or ()]
    if not roots:
        return []
    proc = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", *roots],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"git status failed: {detail}")
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4 or "D" in line[:2]:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        paths.append(path)
    return paths


def _validate_pi_edit_target(vault: Path, contract: dict[str, Any], target: str) -> None:
    frontmatter, _body = split_frontmatter((vault / target).read_text(encoding="utf-8"))
    frontmatter["check_status"] = "unchecked"
    _validate_concept(contract, target, frontmatter)


def _staged_path(vault: Path, target: str) -> Path:
    return vault / ".memoria/staging" / target


def _validate_concept(contract: dict[str, Any], target: str, frontmatter: dict[str, Any]) -> None:
    concept_type = str(frontmatter.get("type") or "")
    schema = contract["types"].get(concept_type)
    if not schema:
        raise ValueError(f"unknown Concept type: {concept_type or '<missing>'}")
    home = str(contract["folders"].get("homes", {}).get(concept_type) or "").strip("/")
    if not home or not target.startswith(home + "/"):
        raise ValueError(f"{concept_type} must live under {home or '<missing home>'}: {target}")
    enums = schema.get("enums") or {}
    for field, spec in (schema.get("required") or {}).items():
        if field not in frontmatter:
            raise ValueError(f"missing required field {field!r} for {concept_type}")
        if not _matches(frontmatter[field], str(spec), enums):
            raise ValueError(f"invalid {field!r} for {concept_type}: expected {spec}")
    check_status = frontmatter.get("check_status")
    if check_status not in {"unchecked", "checked", "quarantined"}:
        raise ValueError(f"invalid check_status: {check_status!r}")


def _write_checked(
    vault: Path,
    target: str,
    output_path: Path,
    frontmatter: dict[str, Any],
    body: str,
    checks: Iterable[str],
    machine: str | None,
    contract: dict[str, Any],
) -> dict[str, Any]:
    promotion_checks = normalize_promotion_checks(checks)
    frontmatter["check_status"] = "checked"
    _validate_concept(contract, target, frontmatter)
    write_frontmatter_doc(output_path, frontmatter, body, create_parent=True)
    events = []
    for check in promotion_checks:
        event = {
            "event": EVENT_CHECK_FIRED,
            "timestamp": now_iso(),
            "check": check,
            "status": "passed",
            "target_id": target,
            "output_sha256": sha256_file(output_path),
        }
        _append_event(vault, machine, event)
        events.append(event)
    state.mark_checked(
        vault,
        target,
        sha256_file(output_path),
        output_path.read_text(encoding="utf-8"),
    )
    if frontmatter.get("type") == "source":
        state.upsert_catalog_source(vault, target, frontmatter)
    return events[0]


def _matches(value: Any, spec: str, enums: dict[str, list[Any]]) -> bool:
    if spec.startswith("literal:"):
        return value == spec.split(":", 1)[1]
    if spec.startswith("enum:"):
        return value in (enums.get(spec.split(":", 1)[1]) or [])
    if spec == "str":
        return isinstance(value, str) and bool(value.strip())
    if spec == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if spec == "bool":
        return isinstance(value, bool)
    if spec == "date":
        return isinstance(value, str | date)
    if spec == "list":
        return isinstance(value, list)
    if spec == "map":
        return isinstance(value, dict)
    return True


def _input_rows(inputs: Iterable[str | dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in inputs:
        if isinstance(item, dict):
            rows.append(dict(item))
        else:
            rows.append({"id": normalize_path(str(item))})
    return rows


def _append_event(vault: Path, machine: str | None, event: dict[str, Any]) -> None:
    append_jsonl(_journal_path(vault, machine), [event])
    state.append_journal_event(vault, event, machine=machine)


def _journal_path(vault: Path, machine: str | None) -> Path:
    name = safe_filename(machine or platform.node() or "local")
    return vault / "journal" / f"{name}.jsonl"


def _iter_events(vault: Path) -> Iterable[dict[str, Any]]:
    for path in sorted((vault / "journal").glob("*.jsonl")):
        yield from iter_jsonl(path)


def _known_current_hashes(vault: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for target, event in rebuild_trace_state(vault).items():
        output_sha = event.get("output_sha256")
        if isinstance(output_sha, str):
            hashes[target] = output_sha
    return hashes


def _latest_derived_inputs(vault: Path, target: str) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for event in _iter_events(vault):
        if event.get("event") == EVENT_DERIVED and event.get("output_id") == target:
            inputs = _input_rows(event.get("inputs") or [])
    return inputs


def _head_sha256(vault: Path, target: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"HEAD:{target}"],
        cwd=vault,
        check=False,
        capture_output=True,
    )
    if proc.returncode:
        return EMPTY_SHA256
    import hashlib

    return "sha256:" + hashlib.sha256(proc.stdout).hexdigest()


def _unique_quarantine_path(path: Path) -> Path:
    candidate = path
    index = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        index += 1
    return candidate


def _commit_relpath(vault: Path, path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.relative_to(vault).as_posix()
    return normalize_path(str(path))


def _git(vault: Path, args: list[str]) -> str:
    proc = subprocess.run(
        args,
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"{' '.join(args)} failed: {detail}")
    return proc.stdout.strip()


def _rel(vault: Path, path: Path) -> str:
    return path.relative_to(vault).as_posix()
