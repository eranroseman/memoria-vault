"""Code run verification helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path


def verify_code_run(vault: Path, run_id: str) -> dict[str, Any]:
    row = state.code_run(vault, run_id)
    if row is None:
        return {"ready": False, "reason": "missing-code-run"}
    if row["state"] != "succeeded":
        return {"ready": False, "reason": row["state"]}
    for relpath, expected in row["output_hashes"].items():
        path = Path(vault) / normalize_path(relpath)
        if not path.is_file() or sha256_file(path) != expected:
            return {"ready": False, "reason": "output-hash-mismatch", "path": relpath}
    return {"ready": True, "run_id": row["run_id"], "artifact_id": row["artifact_id"]}


def code_warrant_complete(
    vault: Path,
    *,
    run_id: str,
    artifact_id: str,
    output_sha256: str,
) -> bool:
    row = state.code_run(vault, run_id)
    if row is None or row["artifact_id"] != artifact_id:
        return False
    if not verify_code_run(vault, run_id).get("ready"):
        return False
    hashes = {str(value) for value in row["output_hashes"].values()}
    hashes.update({str(row.get("stdout_sha256") or ""), str(row.get("stderr_sha256") or "")})
    return output_sha256 in hashes
