"""Content-light local diagnostics for Memoria-owned runtime code."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import tarfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from memoria.runtime.jsonl import append_jsonl, iter_jsonl
from memoria.runtime.time import utc_z

DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_BACKUPS = 3
DIAGNOSTICS_ENV = "MEMORIA_DIAGNOSTICS_DIR"
RAW_ONCE_ENV = "MEMORIA_DIAGNOSTIC_RAW_ONCE"

LEVELS = {"error": 40, "warn": 30, "info": 20, "debug": 10, "trace": 5}
DEFAULT_LEVEL = "warn"

SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.I),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s,}]+"),
    re.compile(r"\b[a-fA-F0-9]{64}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
)


@dataclass(frozen=True)
class PayloadDigest:
    sha256: str
    length: int


def diagnostics_dir() -> Path:
    override = os.environ.get(DIAGNOSTICS_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    state_home = os.environ.get("XDG_STATE_HOME", "").strip()
    base = Path(state_home).expanduser() if state_home else Path.home() / ".local" / "state"
    return base / "memoria" / "diagnostics"


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def assert_outside_vault(path: Path, vault_path: Path | None) -> None:
    if vault_path and _is_relative_to(path, vault_path):
        raise ValueError(f"diagnostic path must be outside the vault: {path}")
    cwd = Path.cwd().resolve()
    if (cwd / ".git").exists() and _is_relative_to(path, cwd):
        raise ValueError(f"diagnostic path must be outside the current Git worktree: {path}")


def _component_level(component: str) -> str:
    specific = os.environ.get(f"MEMORIA_DIAGNOSTIC_LEVEL_{component.upper().replace('-', '_')}", "")
    return (specific or os.environ.get("MEMORIA_DIAGNOSTIC_LEVEL", "") or DEFAULT_LEVEL).lower()


def should_record(component: str, level: str) -> bool:
    threshold = LEVELS.get(_component_level(component), LEVELS[DEFAULT_LEVEL])
    return LEVELS.get(level.lower(), LEVELS["error"]) >= threshold


def payload_digest(payload: Any) -> PayloadDigest:
    if isinstance(payload, bytes):
        raw = payload
    elif isinstance(payload, str):
        raw = payload.encode("utf-8", errors="replace")
    else:
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return PayloadDigest(hashlib.sha256(raw).hexdigest(), len(raw))


def _content_light(value: Any) -> Any:
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str | bytes):
        digest = payload_digest(value)
        return {"sha256": digest.sha256, "length": digest.length}
    if isinstance(value, Mapping):
        return {str(key): _content_light(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_content_light(item) for item in value]
    return _content_light(str(value))


def redact_text(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    home = str(Path.home())
    if home and home in redacted:
        redacted = redacted.replace(home, "~")
    return redacted


def _redacted_payload(payload: Any) -> Any:
    if isinstance(payload, bytes):
        return redact_text(payload.decode("utf-8", errors="replace"))
    if isinstance(payload, str):
        return redact_text(payload)
    return redact_text(json.dumps(payload, sort_keys=True, default=str))


def _log_path(state_dir: Path, now: datetime | None = None) -> Path:
    stamp = (now or datetime.now(UTC)).date().isoformat()
    return state_dir / f"diagnostics-{stamp}.jsonl"


def rotate_logs(
    state_dir: Path, *, max_bytes: int = DEFAULT_MAX_BYTES, backups: int = DEFAULT_BACKUPS
) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(state_dir.glob("diagnostics-*.jsonl")):
        if not path.is_file() or path.stat().st_size <= max_bytes:
            continue
        for old in sorted(state_dir.glob(f"{path.name}.*.gz"), reverse=True):
            suffix = old.name.removeprefix(f"{path.name}.").removesuffix(".gz")
            if suffix.isdigit():
                index = int(suffix)
                if index >= backups:
                    old.unlink(missing_ok=True)
                else:
                    old.rename(path.with_name(f"{path.name}.{index + 1}.gz"))
        rotated = path.with_name(f"{path.name}.1.gz")
        with path.open("rb") as src, gzip.open(rotated, "wb") as dst:
            dst.write(src.read())
        path.unlink(missing_ok=True)


def record_event(
    *,
    component: str,
    level: str,
    code: str,
    payload: Any | None = None,
    details: Mapping[str, Any] | None = None,
    vault_path: Path | None = None,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    level = level.lower()
    if not should_record(component, level):
        return None
    target_dir = state_dir or diagnostics_dir()
    assert_outside_vault(target_dir, vault_path)
    target_dir.mkdir(parents=True, exist_ok=True)
    rotate_logs(target_dir)

    event: dict[str, Any] = {
        "timestamp": utc_z(now),
        "component": component,
        "level": level,
        "code": code,
    }
    if payload is not None:
        digest = payload_digest(payload)
        event["payload_sha256"] = digest.sha256
        event["payload_length"] = digest.length
    if details:
        event["details"] = _content_light(details)
    if payload is not None and os.environ.pop(RAW_ONCE_ENV, "") == "1":
        event["raw_capture"] = "ephemeral-redacted"
        event["payload_redacted"] = _redacted_payload(payload)

    append_jsonl(_log_path(target_dir, now), [event])
    return event


def redaction_self_test() -> None:
    corpus = "\n".join(  # noqa: FLY002 -- list of distinct secret patterns is clearer than one literal
        [
            "Bearer abcdefghijklmnopqrstuvwxyz",
            "OBSIDIAN_API_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            "sk-testsecret0123456789",
            "password: swordfish",
        ]
    )
    redacted = redact_text(corpus)
    forbidden = (
        "abcdefghijklmnopqrstuvwxyz",
        "0123456789abcdef0123456789abcdef",
        "sk-testsecret",
        "swordfish",
    )
    leaked = [item for item in forbidden if item in redacted]
    if leaked:
        raise AssertionError(f"diagnostic redaction leaked known-sensitive strings: {leaked}")


def create_redacted_bundle(
    output: Path,
    *,
    state_dir: Path | None = None,
    include_raw: bool = False,
) -> Path:
    redaction_self_test()
    source_dir = state_dir or diagnostics_dir()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as tar:
        readme = (
            b"Memoria diagnostic bundle.\n"
            b"Review before sharing. Default contents are codes, hashes, lengths, and redacted strings.\n"
        )
        info = tarfile.TarInfo("README.txt")
        info.size = len(readme)
        tar.addfile(info, fileobj=io.BytesIO(readme))
        for path in sorted(source_dir.glob("diagnostics-*.jsonl*")):
            rows = []
            if path.suffix == ".gz":
                with gzip.open(path, "rt", encoding="utf-8") as reader:
                    source_rows = [json.loads(line) for line in reader if line.strip()]
            else:
                source_rows = list(iter_jsonl(path))
            for row in source_rows:
                clean = dict(row)
                if not include_raw:
                    clean.pop("payload_redacted", None)
                    clean.pop("raw_capture", None)
                elif "payload_redacted" in clean:
                    clean["payload_redacted"] = redact_text(str(clean["payload_redacted"]))
                rows.append(json.dumps(clean, sort_keys=True) + "\n")
            data = "".join(rows).encode("utf-8")
            member_name = path.name.removesuffix(".gz").removesuffix(".jsonl") + ".redacted.jsonl"
            info = tarfile.TarInfo(member_name)
            info.size = len(data)
            tar.addfile(info, fileobj=io.BytesIO(data))
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Memoria content-light diagnostics")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--include-raw", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        redaction_self_test()
    if args.bundle:
        create_redacted_bundle(args.bundle, state_dir=args.state_dir, include_raw=args.include_raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
