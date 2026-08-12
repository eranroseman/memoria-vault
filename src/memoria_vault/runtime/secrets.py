"""User-scope secrets file loading and the credentials registry (spec section 4b)."""

from __future__ import annotations

import errno
import os
import re
import stat
from collections.abc import Collection, Iterator, Mapping, MutableMapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from memoria_vault.runtime.paths import path_redirects

_NAME_RE = re.compile(r"[A-Z][A-Z0-9_]*")
_REDIRECT_ERROR = "secrets path must not redirect through a symlink or junction"
_NONREGULAR_ERROR = "secrets target must be a regular file"


def secrets_path() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME", "").strip()
    root = (
        Path(config_home)
        if config_home and Path(config_home).is_absolute()
        else Path.home() / ".config"
    )
    return root / "memoria" / "secrets.env"


def read_secrets_file(path: Path | None = None) -> tuple[dict[str, str], str]:
    target = path or secrets_path()
    if _supports_anchored_secret_reads():
        return _read_secrets_file_anchored(target)
    return _read_secrets_file_fallback(target)


def _supports_anchored_secret_reads() -> bool:
    return os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW")


def _read_secrets_file_anchored(target: Path) -> tuple[dict[str, str], str]:
    parent_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        parent_fd = os.open(target.parent, parent_flags)
    except FileNotFoundError:
        return {}, ""
    except OSError as exc:
        return {}, _read_warning(target, _read_error_reason(exc, "parent"))
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
        fd: int | None = None
        try:
            fd = os.open(target.name, flags, dir_fd=parent_fd)
        except FileNotFoundError:
            return {}, ""
        except OSError as exc:
            return {}, _read_warning(target, _read_error_reason(exc, "target"))
        try:
            mode = os.fstat(fd).st_mode
            if not stat.S_ISREG(mode):
                return {}, _read_warning(target, "target is not a regular file")
            if mode & stat.S_IROTH:
                return {}, _read_warning(
                    target, f"target is world-readable; run: chmod 600 {target}"
                )
            with os.fdopen(fd, "r", encoding="utf-8") as source:
                fd = None
                return _parse_env_text(source.read()), ""
        except (OSError, UnicodeDecodeError):
            return {}, _read_warning(target, "target could not be read")
        finally:
            if fd is not None:
                os.close(fd)
    finally:
        os.close(parent_fd)


def _read_secrets_file_fallback(target: Path) -> tuple[dict[str, str], str]:
    parent = target.parent
    if not parent.exists() and not parent.is_symlink():
        return {}, ""
    if path_redirects(parent) or path_redirects(target):
        return {}, _read_warning(target, "path redirects through a symlink or junction")
    try:
        mode = target.lstat().st_mode
    except FileNotFoundError:
        return {}, ""
    if not stat.S_ISREG(mode):
        return {}, _read_warning(target, "target is not a regular file")
    if mode & stat.S_IROTH:
        return {}, _read_warning(target, f"target is world-readable; run: chmod 600 {target}")
    try:
        with target.open("r", encoding="utf-8") as source:
            return _parse_env_text(source.read()), ""
    except (OSError, UnicodeDecodeError):
        return {}, _read_warning(target, "target could not be read")


def _read_error_reason(exc: OSError, part: str) -> str:
    if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
        return f"{part} redirects through a symlink or is not a directory"
    return f"{part} could not be opened"


def _read_warning(target: Path, reason: str) -> str:
    return f"secrets file {target} {reason}; refusing to load it"


def load_secrets(environ: MutableMapping[str, str] | None = None) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    path = secrets_path()
    values, warning = read_secrets_file(path)
    loaded = [name for name in sorted(values) if name not in env]
    for name in loaded:
        env[name] = values[name]
    return {"path": str(path), "loaded": loaded, "warning": warning}


CREDENTIAL_REGISTRY: tuple[dict[str, str], ...] = (
    {
        "name": "OPENALEX_API_KEY",
        "class": "enhancing",
        "effect_when_unset": "openalex keyless polite-pool mode (lower rate limits)",
    },
    {
        "name": "SEMANTIC_SCHOLAR_API_KEY",
        "class": "enhancing",
        "effect_when_unset": "semanticscholar adapter off (default_on_when_keyed)",
    },
    {
        "name": "PUBMED_API_KEY",
        "class": "enhancing",
        "effect_when_unset": "NCBI keyless tier when the PubMed adapter lands",
    },
    {
        "name": "GITHUB_TOKEN",
        "class": "enhancing",
        "effect_when_unset": "anonymous rate limits; private repos refuse honestly",
    },
    {
        "name": "NCBI_EMAIL",
        "class": "identity",
        "effect_when_unset": "polite-pool identity (mailto/email query params) omitted",
    },
)


def credential_report(
    workspace: Path | None = None,
    *,
    loaded_from_file: Collection[str] | None = None,
) -> list[dict[str, str]]:
    """Return credentials by name, status, and provenance without values."""
    required_names = _runner_key_names(workspace)
    required_set = set(required_names)
    static_entries = [entry for entry in CREDENTIAL_REGISTRY if entry["name"] not in required_set]
    names = [*required_names, *(entry["name"] for entry in static_entries)]
    file_values = (
        read_secrets_file()[0]
        if loaded_from_file is None and any(name not in os.environ for name in names)
        else {}
    )
    rows = [
        _credential_row(
            name,
            "required-for-operation",
            f"live-model calls refuse before the network; set it: memoria secrets set {name}",
            file_values,
            loaded_from_file,
        )
        for name in required_names
    ]
    rows.extend(
        _credential_row(
            entry["name"],
            entry["class"],
            entry["effect_when_unset"],
            file_values,
            loaded_from_file,
        )
        for entry in static_entries
    )
    return rows


def _runner_key_names(workspace: Path | None) -> list[str]:
    if workspace is None:
        return []
    from memoria_vault.runtime.operations import load_runner_provider_config

    try:
        providers = load_runner_provider_config(workspace)
    except (OSError, ValueError):
        return []
    names = {
        key_env
        for spec in providers.values()
        if isinstance(spec, Mapping)
        and isinstance((key_env := spec.get("key_env")), str)
        and _NAME_RE.fullmatch(key_env)
    }
    return sorted(names)


def _credential_row(
    name: str,
    credential_class: str,
    effect_when_unset: str,
    file_values: Mapping[str, str],
    loaded_from_file: Collection[str] | None,
) -> dict[str, str]:
    if loaded_from_file is not None and name in loaded_from_file:
        value, source = os.environ.get(name, ""), "file"
    elif name in os.environ:
        value, source = os.environ[name], "env"
    elif loaded_from_file is None and name in file_values:
        value, source = file_values[name], "file"
    else:
        value, source = "", ""
    return {
        "name": name,
        "class": credential_class,
        "status": "set" if value else "unset",
        "source": source,
        "effect_when_unset": effect_when_unset,
    }


def write_secret(name: str, value: str, path: Path | None = None) -> Path:
    """Atomically upsert one private, user-scope secret without following links."""
    validate_secret_name(name)
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("secret value must be non-empty")
    if "\0" in value or len(value.splitlines()) != 1:
        raise ValueError("secret value must be a single line without control breaks")

    target = path or secrets_path()
    if _supports_anchored_secret_writes():
        try:
            return _write_secret_anchored(target, name, cleaned)
        except NotImplementedError:
            pass
    return _write_secret_fallback(target, name, cleaned)


def validate_secret_name(name: str) -> None:
    """Reject a secret name without reflecting untrusted terminal text."""
    if not _NAME_RE.fullmatch(name):
        raise ValueError("secret name must match [A-Z][A-Z0-9_]*")


def _supports_anchored_secret_writes() -> bool:
    return os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW")


def _write_secret_anchored(target: Path, name: str, value: str) -> Path:
    with _open_secret_parent(target.parent) as parent_fd:
        values = _read_secret_values(parent_fd, target.name)
        values[name] = value
        body = "".join(f"{key}={values[key]}\n" for key in sorted(values)).encode("utf-8")
        temp_name: str
        temp_fd: int | None
        temp_name, temp_fd = _create_private_secret_temp(parent_fd, target.name)
        try:
            _write_all(temp_fd, body)
            os.fsync(temp_fd)
            os.close(temp_fd)
            temp_fd = None
            _replace_secret_atomically(parent_fd, temp_name, target.name)
        except BaseException:
            if temp_fd is not None:
                try:
                    os.close(temp_fd)
                except OSError:
                    pass
            _unlink_temp_only(parent_fd, temp_name)
            raise
    return target


@contextmanager
def _open_secret_parent(parent: Path) -> Iterator[int]:
    if path_redirects(parent):
        raise ValueError(_REDIRECT_ERROR)
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except FileExistsError as exc:
        raise ValueError("secrets parent must be a directory") from exc
    if path_redirects(parent):
        raise ValueError(_REDIRECT_ERROR)

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(parent, flags)
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise ValueError(_REDIRECT_ERROR) from exc
        raise
    try:
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            raise ValueError("secrets parent must be a directory")
        os.fchmod(fd, 0o700)
        yield fd
    finally:
        os.close(fd)


def _read_secret_values(parent_fd: int, target_name: str) -> dict[str, str]:
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    fd: int | None = None
    try:
        fd = os.open(target_name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        return {}
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise ValueError(_REDIRECT_ERROR) from exc
        raise
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError(_NONREGULAR_ERROR)
        with os.fdopen(fd, "r", encoding="utf-8") as source:
            fd = None
            return _parse_env_text(source.read())
    except UnicodeDecodeError as exc:
        raise ValueError("secrets target must contain UTF-8 text") from exc
    finally:
        if fd is not None:
            os.close(fd)


def _create_private_secret_temp(parent_fd: int, target_name: str) -> tuple[str, int]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    for _ in range(100):
        temp_name = f".{target_name}.{os.urandom(16).hex()}.tmp"
        try:
            fd = os.open(temp_name, flags, 0o600, dir_fd=parent_fd)
        except FileExistsError:
            continue
        try:
            os.fchmod(fd, 0o600)
        except BaseException:
            os.close(fd)
            _unlink_temp_only(parent_fd, temp_name)
            raise
        return temp_name, fd
    raise OSError("could not create private secrets staging file")


def _write_all(fd: int, body: bytes) -> None:
    remaining = memoryview(body)
    while remaining:
        written = os.write(fd, remaining)
        if written <= 0:
            raise OSError("failed to write secrets file")
        remaining = remaining[written:]


def _replace_secret_atomically(parent_fd: int, temp_name: str, target_name: str) -> None:
    _reject_redirect_or_nonregular_target(parent_fd, target_name)
    os.replace(temp_name, target_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)


def _reject_redirect_or_nonregular_target(parent_fd: int, target_name: str) -> None:
    try:
        mode = os.stat(target_name, dir_fd=parent_fd, follow_symlinks=False).st_mode
    except FileNotFoundError:
        return
    if stat.S_ISLNK(mode):
        raise ValueError(_REDIRECT_ERROR)
    if not stat.S_ISREG(mode):
        raise ValueError(_NONREGULAR_ERROR)


def _unlink_temp_only(parent_fd: int, temp_name: str) -> None:
    try:
        os.unlink(temp_name, dir_fd=parent_fd)
    except FileNotFoundError:
        pass


def _write_secret_fallback(target: Path, name: str, value: str) -> Path:
    parent = target.parent
    if path_redirects(parent):
        raise ValueError(_REDIRECT_ERROR)
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except FileExistsError as exc:
        raise ValueError("secrets parent must be a directory") from exc
    if path_redirects(parent):
        raise ValueError(_REDIRECT_ERROR)
    if not parent.is_dir():
        raise ValueError("secrets parent must be a directory")
    os.chmod(parent, 0o700)

    values = _read_secret_values_fallback(target)
    values[name] = value
    body = "".join(f"{key}={values[key]}\n" for key in sorted(values)).encode("utf-8")
    temp_path: Path
    temp_fd: int | None
    temp_path, temp_fd = _create_private_secret_temp_fallback(parent, target.name)
    try:
        _write_all(temp_fd, body)
        os.fsync(temp_fd)
        os.close(temp_fd)
        temp_fd = None
        _reject_redirect_or_nonregular_target_fallback(target)
        os.replace(temp_path, target)
    except BaseException:
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except OSError:
                pass
        temp_path.unlink(missing_ok=True)
        raise
    return target


def _read_secret_values_fallback(target: Path) -> dict[str, str]:
    if not target.exists() and not target.is_symlink():
        return {}
    _reject_redirect_or_nonregular_target_fallback(target)
    try:
        return _parse_env_text(target.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("secrets target must contain UTF-8 text") from exc


def _create_private_secret_temp_fallback(parent: Path, target_name: str) -> tuple[Path, int]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    for _ in range(100):
        temp_path = parent / f".{target_name}.{os.urandom(16).hex()}.tmp"
        try:
            fd = os.open(temp_path, flags, 0o600)
        except FileExistsError:
            continue
        try:
            os.chmod(temp_path, 0o600)
        except BaseException:
            os.close(fd)
            temp_path.unlink(missing_ok=True)
            raise
        return temp_path, fd
    raise OSError("could not create private secrets staging file")


def _reject_redirect_or_nonregular_target_fallback(target: Path) -> None:
    if path_redirects(target):
        raise ValueError(_REDIRECT_ERROR)
    try:
        mode = target.lstat().st_mode
    except FileNotFoundError:
        return
    if not stat.S_ISREG(mode):
        raise ValueError(_NONREGULAR_ERROR)


def _parse_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, _, value = stripped.partition("=")
        name = name.strip()
        if not _NAME_RE.fullmatch(name):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if "\0" in value:
            continue
        values[name] = value
    return values
