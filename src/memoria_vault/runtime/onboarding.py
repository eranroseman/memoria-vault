"""Onboarding runway: Obsidian detect/install/open, Zotero probe, notices.

Bootstrap spec section 7: machine wiring + entry choreography only. Every
process boundary (prompts, subprocesses, HTTP) is an injectable parameter
with a production default, so each branch is testable without patching.
"""

from __future__ import annotations

import subprocess
import urllib.parse
from collections.abc import Callable, Mapping
from pathlib import Path

RunFn = Callable[..., subprocess.CompletedProcess[str]]
AskFn = Callable[[str], str]
SayFn = Callable[[str], None]

OBSIDIAN_DOWNLOAD_URL = "https://obsidian.md/download"

# Frozen allowlist (bootstrap spec section 7.1): the command is shown
# verbatim and run only on explicit yes. The engine never downloads
# binaries itself; anything off this list is detect-and-direct.
OBSIDIAN_INSTALL_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "darwin": ("brew", "install", "--cask", "obsidian"),
    "windows": ("winget", "install", "Obsidian.Obsidian"),
    "linux": ("flatpak", "install", "md.obsidian.Obsidian"),
}

# Package-manager installs (unlike the quick `_detect_linux` version probe)
# can legitimately take minutes to download; this only bounds a stalled
# process so onboarding can never hang forever.
_INSTALL_TIMEOUT_S = 300


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


def offer_obsidian_install(
    sys_platform: str,
    *,
    ask: AskFn,
    say: SayFn,
    run: RunFn = subprocess.run,
) -> str:
    """Offer to install Obsidian via the frozen per-platform allowlist.

    The command run, if any, is always the literal tuple looked up from
    ``OBSIDIAN_INSTALL_ALLOWLIST`` for the resolved platform key — never a
    value derived from ``ask``'s answer or any other input. Nothing runs
    without an explicit "y"/"yes" answer; any other answer, including EOF or
    an ambiguous response, is treated as a decline.
    """
    command = OBSIDIAN_INSTALL_ALLOWLIST.get(platform_key(sys_platform) or "")
    if command is None:
        say(f"Obsidian not detected. Download it from {OBSIDIAN_DOWNLOAD_URL}")
        return "manual"
    say("Obsidian not detected. Memoria can install it with:")
    say(f"  {' '.join(command)}")
    try:
        answer = ask("Run this command now? [y/N] ").strip().lower()
    except EOFError:
        answer = ""
    if answer not in ("y", "yes"):
        say(f"Skipped. Download Obsidian from {OBSIDIAN_DOWNLOAD_URL}")
        return "declined"
    try:
        result = run(list(command), check=False, timeout=_INSTALL_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        say(
            f"Install command did not finish within {_INSTALL_TIMEOUT_S}s. "
            f"Download Obsidian from {OBSIDIAN_DOWNLOAD_URL}"
        )
        return "failed"
    except OSError:
        say(f"{command[0]} is not available. Download Obsidian from {OBSIDIAN_DOWNLOAD_URL}")
        return "manual"
    if result.returncode != 0:
        say(
            f"Install command exited {result.returncode}. "
            f"Download Obsidian from {OBSIDIAN_DOWNLOAD_URL}"
        )
        return "failed"
    return "installed"


MANUAL_OPEN_FALLBACK = "Open Obsidian → Open folder as vault → {path}"


def open_vault_in_obsidian(
    workspace: Path,
    *,
    sys_platform: str,
    run: RunFn = subprocess.run,
    say: SayFn = print,
) -> str:
    """Open the vault in Obsidian via the ``obsidian://open`` URI.

    Deep-links to ``<workspace>/Start here.md`` when that file exists, else
    the vault root (spec §7.3). The path is percent-encoded with an empty
    ``safe`` set so nothing in it — including ``&``/``=`` — can inject an
    additional URI parameter; a zero exit from the opener does not prove
    Obsidian actually registered the vault, so the verbatim manual fallback
    is always shown alongside a successful launch, not just on failure.
    """
    start_here = workspace / "Start here.md"
    open_target = start_here if start_here.is_file() else workspace
    uri = "obsidian://open?path=" + urllib.parse.quote(str(open_target), safe="")
    fallback = MANUAL_OPEN_FALLBACK.format(path=workspace)
    key = platform_key(sys_platform)
    openers = {
        "darwin": ["open", uri],
        "windows": ["cmd", "/c", "start", "", uri],
        "linux": ["xdg-open", uri],
    }
    opener = openers.get(key or "")
    if opener is None:
        say(fallback)
        return "manual"
    try:
        result = run(
            opener,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        result = None
    if result is None or result.returncode != 0:
        say(fallback)
        return "manual"
    say(f"Opening {uri}")
    say(f"If Obsidian shows no vault: {fallback}")
    return "opened"
