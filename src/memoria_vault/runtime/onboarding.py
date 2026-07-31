"""Onboarding runway: Obsidian detect/install/open, Zotero probe, notices.

Bootstrap spec section 7: machine wiring + entry choreography only. Every
process boundary (prompts, subprocesses, HTTP) is an injectable parameter
with a production default, so each branch is testable without patching.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

RunFn = Callable[..., subprocess.CompletedProcess[str]]
AskFn = Callable[[str], str]
SayFn = Callable[[str], None]


def platform_key(sys_platform: str) -> str | None:
    if sys_platform == "darwin":
        return "darwin"
    if sys_platform.startswith("win") or sys_platform == "cygwin":
        return "windows"
    if sys_platform.startswith("linux"):
        return "linux"
    return None


def detect_obsidian(
    sys_platform: str,
    *,
    env: Mapping[str, str],
    home: Path,
    run: RunFn = subprocess.run,
) -> bool:
    key = platform_key(sys_platform)
    if key == "darwin":
        return _detect_macos((Path("/Applications"), home / "Applications"))
    if key == "windows":
        return _detect_windows(env)
    if key == "linux":
        return _detect_linux(run, _linux_data_dirs(env, home))
    return False


def _detect_macos(app_dirs: tuple[Path, ...]) -> bool:
    return any((app_dir / "Obsidian.app").is_dir() for app_dir in app_dirs)


def _detect_windows(env: Mapping[str, str]) -> bool:
    local_appdata = env.get("LOCALAPPDATA", "")
    if local_appdata and (Path(local_appdata) / "Obsidian" / "Obsidian.exe").is_file():
        return True
    return _windows_registry_has_obsidian()


def _windows_registry_has_obsidian() -> bool:
    try:
        import winreg
    except ImportError:
        return False
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Obsidian"
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            winreg.CloseKey(winreg.OpenKey(root, key_path))
        except OSError:
            continue
        return True
    return False


def _linux_data_dirs(env: Mapping[str, str], home: Path) -> tuple[Path, ...]:
    dirs = [Path(env.get("XDG_DATA_HOME") or home / ".local/share")]
    dirs.extend(
        Path(part)
        for part in (env.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":")
        if part
    )
    dirs.append(Path("/var/lib/flatpak/exports/share"))
    return tuple(dirs)


def _detect_linux(run: RunFn, data_dirs: tuple[Path, ...]) -> bool:
    try:
        probe = run(
            ["flatpak", "info", "md.obsidian.Obsidian"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        probe = None
    if probe is not None and probe.returncode == 0:
        return True
    entries = ("obsidian.desktop", "md.obsidian.Obsidian.desktop")
    return any(
        (data_dir / "applications" / entry).is_file() for data_dir in data_dirs for entry in entries
    )
