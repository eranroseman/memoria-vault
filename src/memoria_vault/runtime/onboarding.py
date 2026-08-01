"""Onboarding runway: Obsidian detect/install/open, Zotero probe, notices.

Bootstrap spec section 7: machine wiring + entry choreography only. Every
process boundary (prompts, subprocesses, HTTP) is an injectable parameter
with a production default, so each branch is testable without patching.
"""

from __future__ import annotations

import http.client
import subprocess
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from memoria_vault.runtime.rendezvous import _NoRedirect

RunFn = Callable[..., subprocess.CompletedProcess[str]]
AskFn = Callable[[str], str]
SayFn = Callable[[str], None]

OBSIDIAN_DOWNLOAD_URL = "https://obsidian.md/download"

# Shared verbatim so `offer_obsidian_install`'s own decline and
# `run_onboarding`'s ask-failure fallback cannot silently drift apart.
OBSIDIAN_SKIPPED_MESSAGE = f"Skipped. Download Obsidian from {OBSIDIAN_DOWNLOAD_URL}"

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


def _safe_is_dir(path: Path) -> bool:
    """``Path.is_dir`` that treats an unreadable path as "not found".

    ``pathlib`` only swallows ``ENOENT``/``ENOTDIR``/``EBADF``/``ELOOP``
    internally; every other ``OSError`` -- notably ``PermissionError``
    (``EACCES``) from a directory in the path that exists but cannot be
    traversed, e.g. an XDG data dir under a root-only mount -- propagates.
    A detection probe that cannot read a directory should report "not
    found", the truthful answer, rather than crash its caller.
    """
    try:
        return path.is_dir()
    except OSError:
        return False


def _safe_is_file(path: Path) -> bool:
    """``Path.is_file`` counterpart to ``_safe_is_dir``; see its docstring."""
    try:
        return path.is_file()
    except OSError:
        return False


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
    return any(_safe_is_dir(app_dir / "Obsidian.app") for app_dir in app_dirs)


def _detect_windows(env: Mapping[str, str]) -> bool:
    local_appdata = env.get("LOCALAPPDATA", "")
    if local_appdata and _safe_is_file(Path(local_appdata) / "Obsidian" / "Obsidian.exe"):
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
        _safe_is_file(data_dir / "applications" / entry)
        for data_dir in data_dirs
        for entry in entries
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
        say(OBSIDIAN_SKIPPED_MESSAGE)
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
    open_target = start_here if _safe_is_file(start_here) else workspace
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


ZOTERO_CONNECTOR_URL = "http://127.0.0.1:23119/connector/ping"


def _open_zotero_probe(url: str, *, timeout: float) -> Any:
    """Open the Zotero probe without ambient proxy or redirect policy.

    Same shape as ``rendezvous._open_lifecycle_request``: a bare ``urlopen``
    honors ``http_proxy``/``https_proxy`` even for a ``127.0.0.1`` target
    (``urllib.request.proxy_bypass`` does not exempt loopback addresses), so
    under a corporate or dev-container proxy this request would leave the
    machine, and a proxy answering any 2xx (captive portal, interstitial)
    would report Zotero running with none present — defeating the loopback
    literal far more thoroughly than the hosts-file override it guards
    against. ``ProxyHandler({})`` forces the direct connection the literal
    was meant to guarantee; ``_NoRedirect`` stops a redirected connector
    endpoint from being followed to another host.
    """
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    return opener.open(url, timeout=timeout)


def zotero_running(
    *,
    url_open: Callable[..., Any] = _open_zotero_probe,
    timeout: float = 0.5,
) -> bool:
    """Probe the local Zotero Connector on 127.0.0.1:23119 (bootstrap spec §7.4).

    ``127.0.0.1`` is used verbatim rather than ``localhost``, which can
    resolve to IPv6 ``::1`` or hit a hosts-file override and silently miss
    the connector; the default ``url_open`` additionally opens through a
    proxy-free, redirect-free opener (see ``_open_zotero_probe``) so an
    ambient proxy cannot intercept or redirect the loopback request. Must
    never raise: a probe that crashes onboarding is the failure mode this
    section keeps hitting. ``urlopen`` collapses to ``OSError`` subclasses
    (``URLError``, ``HTTPError``, ``TimeoutError`` — ``socket.timeout`` is
    its alias —, ``ConnectionRefusedError``, ...), but
    ``http.client.HTTPException`` (a malformed response, e.g. a bad status
    line) is a plain ``Exception``, not an ``OSError`` subclass, and the
    ``int(status)`` coercion below can raise ``ValueError`` on a malformed
    status value or ``TypeError`` on a non-numeric status type; all branches
    are caught explicitly.
    """
    try:
        with url_open(ZOTERO_CONNECTOR_URL, timeout=timeout) as response:
            status = getattr(response, "status", None)
            return status is None or 200 <= int(status) < 300
    except (OSError, TypeError, ValueError, http.client.HTTPException):
        return False


ZOTERO_HOWTO_URL = "https://eranroseman.github.io/memoria-vault/how-to-guides/setup/set-up-zotero"

CREDENTIALS_NOTICE = (
    "Optional: live-model operations need a provider key — set one with "
    "`memoria secrets set <NAME>` (check `memoria doctor` for credential "
    "status); offline and keyless modes need nothing."
)


def run_onboarding(
    workspace: Path,
    *,
    sys_platform: str,
    env: Mapping[str, str],
    home: Path,
    ask: AskFn,
    say: SayFn,
    run: RunFn = subprocess.run,
    url_open: Callable[..., Any] = _open_zotero_probe,
) -> dict[str, Any]:
    """Run the full onboarding runway once (bootstrap spec section 7).

    Sequences every BOOT-D.1-D.4 probe/action into one step log: detect or
    offer to install Obsidian, open the vault when Obsidian is present, probe
    for a running Zotero connector, and always surface the credentials
    notice. ``url_open`` defaults to the hardened, proxy-free/redirect-free
    ``_open_zotero_probe`` (not a bare ``urllib.request.urlopen``) and is
    forwarded verbatim to ``zotero_running`` so a caller that does not
    override it still gets BOOT-D.4's hardening rather than silently losing
    it.

    ``ok`` is unconditionally ``True``: every step status here is an honest
    outcome (including a decline or a failed install) rather than a crash,
    so a caller such as the future ``memoria onboard`` CLI's ``_emit`` never
    prints a spurious FAILED for a normal manual-fallback path. ``completed``
    is the one place that distinction actually matters: it is ``True`` only
    when Obsidian is present/installed *and* the vault was actually opened.
    """
    steps: list[dict[str, str]] = []

    if detect_obsidian(sys_platform, env=env, home=home, run=run):
        obsidian_status = "present"
    else:
        try:
            obsidian_status = offer_obsidian_install(sys_platform, ask=ask, say=say, run=run)
        except (EOFError, RuntimeError):
            # `ask` is not total. `offer_obsidian_install` only guards its own
            # `ask()` call against `EOFError`. Some closed-stdin shapes raise
            # something else instead: fd 0 closed, or `sys.stdin = None`,
            # makes builtin `input()` raise `RuntimeError: input(): lost
            # sys.stdin`, which this catches too so it cannot otherwise
            # propagate out of this function and crash the whole onboarding
            # sequence. Other closed-stdin shapes still escape uncaught --
            # an in-process `sys.stdin.close()` raises `ValueError: I/O
            # operation on closed file`, and a pytest-style capture raises
            # `OSError` -- neither is a `RuntimeError`/`EOFError`. Whatever
            # does land here is treated the same as a decline: an honest
            # "no consent obtained" outcome.
            say(OBSIDIAN_SKIPPED_MESSAGE)
            obsidian_status = "declined"
    steps.append({"step": "obsidian", "status": obsidian_status})

    if obsidian_status in ("present", "installed"):
        open_status = open_vault_in_obsidian(workspace, sys_platform=sys_platform, run=run, say=say)
    else:
        open_status = "skipped"
        say(MANUAL_OPEN_FALLBACK.format(path=workspace))
    steps.append({"step": "open-vault", "status": open_status})

    if zotero_running(url_open=url_open):
        say(f"Zotero detected on 127.0.0.1:23119 — connect it: {ZOTERO_HOWTO_URL}")
        zotero_status = "offered"
    else:
        zotero_status = "not-detected"
    steps.append({"step": "zotero", "status": zotero_status})

    say(CREDENTIALS_NOTICE)
    steps.append({"step": "credentials", "status": "noticed"})

    completed = obsidian_status in ("present", "installed") and open_status == "opened"
    return {
        "ok": True,
        "workspace": str(workspace),
        "completed": completed,
        "steps": steps,
    }
