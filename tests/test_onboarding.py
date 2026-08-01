"""Onboarding runway unit tests: injected IO for every probe (bootstrap spec section 7)."""

from __future__ import annotations

import http.client
import inspect
import socket
import subprocess
import threading
import urllib.error
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from memoria_vault.runtime import onboarding


class FakeRun:
    def __init__(self, returncode: int = 0, raises: Exception | None = None) -> None:
        self.calls: list[list[str]] = []
        self.kwargs: list[dict[str, object]] = []
        self.returncode = returncode
        self.raises = raises

    def __call__(self, argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
        self.kwargs.append(kwargs)
        if self.raises is not None:
            raise self.raises
        return subprocess.CompletedProcess(argv, self.returncode, stdout="", stderr="")


def test_platform_key_normalizes_supported_platforms() -> None:
    assert onboarding.platform_key("darwin") == "darwin"
    assert onboarding.platform_key("win32") == "windows"
    assert onboarding.platform_key("cygwin") == "windows"
    assert onboarding.platform_key("linux") == "linux"
    assert onboarding.platform_key("freebsd14") is None


def test_detect_macos_finds_app_bundle(tmp_path: Path) -> None:
    apps = tmp_path / "Applications"
    (apps / "Obsidian.app").mkdir(parents=True)

    assert onboarding._detect_macos((apps,)) is True
    assert onboarding._detect_macos((tmp_path / "empty",)) is False


def test_detect_windows_uses_localappdata_presence(tmp_path: Path) -> None:
    exe = tmp_path / "Obsidian" / "Obsidian.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")

    assert onboarding._detect_windows({"LOCALAPPDATA": str(tmp_path)}) is True
    assert onboarding._detect_windows({"LOCALAPPDATA": str(tmp_path / "missing")}) is False
    assert onboarding._detect_windows({}) is False


def test_detect_linux_accepts_flatpak_probe(tmp_path: Path) -> None:
    run = FakeRun(returncode=0)

    assert onboarding._detect_linux(run, (tmp_path,)) is True
    assert run.calls == [["flatpak", "info", "md.obsidian.Obsidian"]]


def test_detect_linux_falls_back_to_desktop_entry(tmp_path: Path) -> None:
    run = FakeRun(raises=FileNotFoundError("flatpak"))
    entry = tmp_path / "applications" / "md.obsidian.Obsidian.desktop"
    entry.parent.mkdir(parents=True)
    entry.write_text("[Desktop Entry]\n", encoding="utf-8")

    assert onboarding._detect_linux(run, (tmp_path,)) is True
    assert onboarding._detect_linux(FakeRun(returncode=1), (tmp_path / "empty",)) is False


def test_detect_obsidian_dispatches_linux_and_rejects_unknown(tmp_path: Path) -> None:
    home = tmp_path / "home"
    entry = home / ".local/share/applications/obsidian.desktop"
    entry.parent.mkdir(parents=True)
    entry.write_text("[Desktop Entry]\n", encoding="utf-8")
    run = FakeRun(returncode=1)

    assert onboarding.detect_obsidian("linux", env={}, home=home, run=run) is True
    assert onboarding.detect_obsidian("plan9", env={}, home=home, run=run) is False


def test_detect_obsidian_dispatches_macos(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / "Applications" / "Obsidian.app").mkdir(parents=True)

    assert onboarding.detect_obsidian("darwin", env={}, home=home, run=FakeRun()) is True
    assert (
        onboarding.detect_obsidian("darwin", env={}, home=tmp_path / "elsewhere", run=FakeRun())
        is False
    )


def test_detect_obsidian_dispatches_windows(tmp_path: Path) -> None:
    home = tmp_path / "home"
    exe = tmp_path / "appdata" / "Obsidian" / "Obsidian.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")

    assert (
        onboarding.detect_obsidian(
            "win32", env={"LOCALAPPDATA": str(tmp_path / "appdata")}, home=home, run=FakeRun()
        )
        is True
    )
    assert onboarding.detect_obsidian("win32", env={}, home=home, run=FakeRun()) is False


def test_install_allowlist_is_frozen_verbatim() -> None:
    assert onboarding.OBSIDIAN_INSTALL_ALLOWLIST == {
        "darwin": ("brew", "install", "--cask", "obsidian"),
        "windows": ("winget", "install", "Obsidian.Obsidian"),
        "linux": ("flatpak", "install", "md.obsidian.Obsidian"),
    }


def test_offer_install_shows_command_then_runs_on_yes() -> None:
    run = FakeRun(returncode=0)
    said: list[str] = []
    prompts: list[str] = []

    def ask(prompt: str) -> str:
        prompts.append(prompt)
        return "y"

    status = onboarding.offer_obsidian_install("linux", ask=ask, say=said.append, run=run)

    assert status == "installed"
    assert run.calls == [["flatpak", "install", "md.obsidian.Obsidian"]]
    # The exact command is shown verbatim, and consent is asked, before it runs.
    assert "  flatpak install md.obsidian.Obsidian" in said
    assert prompts == ["Run this command now? [y/N] "]


def test_offer_install_declines_without_running() -> None:
    run = FakeRun(returncode=0)
    said: list[str] = []

    status = onboarding.offer_obsidian_install(
        "darwin", ask=lambda _prompt: "n", say=said.append, run=run
    )

    assert status == "declined"
    assert run.calls == []
    assert any(onboarding.OBSIDIAN_DOWNLOAD_URL in line for line in said)


def test_offer_install_treats_eof_as_decline() -> None:
    run = FakeRun(returncode=0)

    def ask(_prompt: str) -> str:
        raise EOFError

    status = onboarding.offer_obsidian_install("win32", ask=ask, say=lambda _line: None, run=run)

    assert status == "declined"
    assert run.calls == []


def test_offer_install_directs_to_download_when_no_allowlisted_manager() -> None:
    said: list[str] = []

    status = onboarding.offer_obsidian_install(
        "plan9", ask=lambda _prompt: "y", say=said.append, run=FakeRun()
    )

    assert status == "manual"
    assert any(onboarding.OBSIDIAN_DOWNLOAD_URL in line for line in said)


def test_offer_install_reports_missing_manager_and_nonzero_exit() -> None:
    said: list[str] = []
    missing = onboarding.offer_obsidian_install(
        "linux", ask=lambda _prompt: "y", say=said.append, run=FakeRun(raises=FileNotFoundError())
    )
    failed = onboarding.offer_obsidian_install(
        "linux", ask=lambda _prompt: "y", say=said.append, run=FakeRun(returncode=1)
    )

    assert missing == "manual"
    assert failed == "failed"
    assert sum(onboarding.OBSIDIAN_DOWNLOAD_URL in line for line in said) >= 2


def test_offer_install_treats_hang_as_failed_not_a_crash() -> None:
    # A hanging installer (subprocess.run(..., timeout=...) expiring) must
    # never propagate and crash onboarding; it is reported the same as any
    # other failed install, with the manual fallback shown.
    said: list[str] = []

    status = onboarding.offer_obsidian_install(
        "linux",
        ask=lambda _prompt: "y",
        say=said.append,
        run=FakeRun(raises=subprocess.TimeoutExpired(cmd="flatpak", timeout=1)),
    )

    assert status == "failed"
    assert any(onboarding.OBSIDIAN_DOWNLOAD_URL in line for line in said)


@pytest.mark.parametrize("key", sorted(onboarding.OBSIDIAN_INSTALL_ALLOWLIST))
def test_offer_install_runs_exactly_the_allowlisted_argv_on_consent(key: str) -> None:
    # The allowlist is frozen: on every platform, a "y" answer runs the
    # literal allowlisted tuple for that platform — never anything derived
    # from the answer or any other input.
    run = FakeRun(returncode=0)

    status = onboarding.offer_obsidian_install(
        key, ask=lambda _prompt: "y", say=lambda _line: None, run=run
    )

    assert status == "installed"
    assert run.calls == [list(onboarding.OBSIDIAN_INSTALL_ALLOWLIST[key])]


def test_offer_install_declines_a_command_injection_shaped_answer() -> None:
    # An injection-shaped answer is still just "not y/yes": consent is an
    # exact-match comparison, so it declines without ever reaching `run`.
    run = FakeRun(returncode=0)

    status = onboarding.offer_obsidian_install(
        "darwin",
        ask=lambda _prompt: "y; rm -rf /",
        say=lambda _line: None,
        run=run,
    )

    assert status == "declined"
    assert run.calls == []


def test_open_vault_uses_xdg_open_with_encoded_uri(tmp_path: Path) -> None:
    run = FakeRun(returncode=0)
    said: list[str] = []

    status = onboarding.open_vault_in_obsidian(
        tmp_path, sys_platform="linux", run=run, say=said.append
    )

    expected_uri = "obsidian://open?path=" + urllib.parse.quote(str(tmp_path), safe="")
    assert status == "opened"
    assert run.calls == [["xdg-open", expected_uri]]
    # A zero exit does not prove Obsidian registered a new vault: the
    # verbatim manual fallback is always shown.
    fallback = onboarding.MANUAL_OPEN_FALLBACK.format(path=tmp_path)
    assert any(fallback in line for line in said)


def test_open_vault_deep_links_start_here_when_present(tmp_path: Path) -> None:
    (tmp_path / "Start here.md").write_text("# Start here\n", encoding="utf-8")
    run = FakeRun(returncode=0)

    onboarding.open_vault_in_obsidian(tmp_path, sys_platform="darwin", run=run, say=lambda _l: None)

    expected_uri = "obsidian://open?path=" + urllib.parse.quote(
        str(tmp_path / "Start here.md"), safe=""
    )
    assert run.calls == [["open", expected_uri]]


def test_open_vault_prints_verbatim_fallback_when_uri_bounces(tmp_path: Path) -> None:
    said: list[str] = []

    status = onboarding.open_vault_in_obsidian(
        tmp_path, sys_platform="linux", run=FakeRun(raises=FileNotFoundError()), say=said.append
    )

    assert status == "manual"
    assert onboarding.MANUAL_OPEN_FALLBACK.format(path=tmp_path) in said


def test_open_vault_unsupported_platform_is_manual(tmp_path: Path) -> None:
    said: list[str] = []

    status = onboarding.open_vault_in_obsidian(
        tmp_path, sys_platform="plan9", run=FakeRun(), say=said.append
    )

    assert status == "manual"
    assert onboarding.MANUAL_OPEN_FALLBACK.format(path=tmp_path) in said


def test_open_vault_uses_windows_start_command(tmp_path: Path) -> None:
    run = FakeRun(returncode=0)

    status = onboarding.open_vault_in_obsidian(
        tmp_path, sys_platform="win32", run=run, say=lambda _l: None
    )

    expected_uri = "obsidian://open?path=" + urllib.parse.quote(str(tmp_path), safe="")
    assert status == "opened"
    assert run.calls == [["cmd", "/c", "start", "", expected_uri]]


def test_open_vault_redirects_output_to_devnull_and_never_passes_shell(tmp_path: Path) -> None:
    # capture_output=True would wait for EOF on the pipes rather than the
    # child's exit: a GUI opener that daemonizes (xdg-open's normal shape)
    # inherits the fds and holds them open, so run() would block for the
    # full timeout even though the opener already exited 0. DEVNULL avoids
    # that trap; this pins the redirection so it cannot silently regress.
    run = FakeRun(returncode=0)

    onboarding.open_vault_in_obsidian(tmp_path, sys_platform="linux", run=run, say=lambda _l: None)

    assert run.kwargs == [
        {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "check": False,
            "timeout": 20,
        }
    ]
    assert "shell" not in run.kwargs[0]


def test_open_vault_timeout_expired_falls_back_to_manual_without_raising(tmp_path: Path) -> None:
    said: list[str] = []

    status = onboarding.open_vault_in_obsidian(
        tmp_path,
        sys_platform="linux",
        run=FakeRun(raises=subprocess.TimeoutExpired(cmd="xdg-open", timeout=20)),
        say=said.append,
    )

    assert status == "manual"
    assert onboarding.MANUAL_OPEN_FALLBACK.format(path=tmp_path) in said


def test_open_vault_nonzero_exit_falls_back_to_manual(tmp_path: Path) -> None:
    said: list[str] = []

    status = onboarding.open_vault_in_obsidian(
        tmp_path, sys_platform="linux", run=FakeRun(returncode=1), say=said.append
    )

    assert status == "manual"
    assert onboarding.MANUAL_OPEN_FALLBACK.format(path=tmp_path) in said


@pytest.mark.parametrize(
    "hostile",
    [
        "vault&admin=1",
        "vault?x=1",
        "vault#frag",
        "vault=path",
        "vault%26encoded",
        "vault with spaces",
        "vault-☃-unicode",
        "..",
        "vaultobsidian://open?path=/etc",
    ],
)
def test_open_vault_uri_encoding_cannot_inject_params_or_change_action(
    tmp_path: Path, hostile: str
) -> None:
    # The property that matters is not "safe='' was used" (an implementation
    # detail) but that no hostile workspace path can add a query key, set a
    # fragment, or change the scheme/action. Prove it structurally instead of
    # restating the encoding call.
    workspace = tmp_path / hostile
    run = FakeRun(returncode=0)

    onboarding.open_vault_in_obsidian(workspace, sys_platform="linux", run=run, say=lambda _l: None)

    uri = run.calls[0][1]
    parts = urllib.parse.urlsplit(uri)
    query = urllib.parse.parse_qs(parts.query, keep_blank_values=True)

    assert parts.scheme == "obsidian"
    assert parts.netloc == "open"
    assert parts.fragment == ""
    assert set(query) == {"path"}
    assert query["path"] == [str(workspace)]


class FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


class MalformedStatusResponse:
    """A response whose ``status`` cannot be coerced to ``int``.

    Covers the ``ValueError`` path a malformed connector reply can take.
    """

    status = "not-a-number"

    def __enter__(self) -> MalformedStatusResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


def test_zotero_probe_hits_connector_ping_with_short_timeout() -> None:
    calls: list[tuple[str, float]] = []

    def url_open(url: str, timeout: float = 0.0) -> FakeResponse:
        calls.append((url, timeout))
        return FakeResponse(200)

    assert onboarding.zotero_running(url_open=url_open) is True
    assert calls == [("http://127.0.0.1:23119/connector/ping", 0.5)]


def test_zotero_probe_forwards_a_custom_timeout() -> None:
    # Regression guard: BOOT-D.3 shipped a fake that discarded its kwargs, so
    # nothing pinned that `timeout=` was actually forwarded. Use a non-default
    # value so a dropped/hardcoded timeout fails this assertion.
    calls: list[tuple[str, float]] = []

    def url_open(url: str, timeout: float = 0.0) -> FakeResponse:
        calls.append((url, timeout))
        return FakeResponse(200)

    assert onboarding.zotero_running(url_open=url_open, timeout=2.5) is True
    assert calls == [("http://127.0.0.1:23119/connector/ping", 2.5)]


def test_zotero_probe_uses_loopback_literal_not_localhost() -> None:
    # 127.0.0.1 is not localhost: localhost can resolve to IPv6 ::1 or hit a
    # hosts-file override. Pin the literal the contract specifies.
    assert onboarding.ZOTERO_CONNECTOR_URL == "http://127.0.0.1:23119/connector/ping"


@pytest.mark.parametrize(
    "kind",
    ["off-range-status", "204-no-content"],
)
def test_zotero_probe_reads_status_from_response(kind: str) -> None:
    def url_open(_url: str, timeout: float = 0.0) -> FakeResponse:
        return FakeResponse(500 if kind == "off-range-status" else 204)

    expected = kind == "204-no-content"
    assert onboarding.zotero_running(url_open=url_open) is expected


def test_zotero_probe_is_false_when_connection_refused() -> None:
    def url_open(_url: str, timeout: float = 0.0) -> FakeResponse:
        raise OSError("connection refused")

    assert onboarding.zotero_running(url_open=url_open) is False


def test_zotero_probe_is_false_on_connection_refused_error_subclass() -> None:
    def url_open(_url: str, timeout: float = 0.0) -> FakeResponse:
        raise ConnectionRefusedError("connection refused")

    assert onboarding.zotero_running(url_open=url_open) is False


def test_zotero_probe_is_false_on_url_error() -> None:
    def url_open(_url: str, timeout: float = 0.0) -> FakeResponse:
        raise urllib.error.URLError("no route to host")

    assert onboarding.zotero_running(url_open=url_open) is False


def test_zotero_probe_is_false_on_http_error() -> None:
    def url_open(_url: str, timeout: float = 0.0) -> FakeResponse:
        raise urllib.error.HTTPError(
            "http://127.0.0.1:23119/connector/ping", 500, "boom", None, None
        )

    assert onboarding.zotero_running(url_open=url_open) is False


def test_zotero_probe_is_false_on_timeout_error() -> None:
    def url_open(_url: str, timeout: float = 0.0) -> FakeResponse:
        raise TimeoutError("timed out")

    assert onboarding.zotero_running(url_open=url_open) is False


def test_zotero_probe_is_false_on_socket_timeout_alias() -> None:
    # socket.timeout is an alias of TimeoutError (an OSError subclass) as of
    # Python 3.10, but pin it explicitly via the alias so a runtime downgrade
    # cannot silently reopen this gap.
    def url_open(_url: str, timeout: float = 0.0) -> FakeResponse:
        raise socket.timeout("timed out")  # noqa: UP041 -- deliberately the alias, not TimeoutError

    assert onboarding.zotero_running(url_open=url_open) is False


def test_zotero_probe_is_false_on_http_client_exception_not_an_oserror() -> None:
    # http.client.HTTPException is NOT an OSError subclass (unlike
    # ConnectionRefusedError/TimeoutError/URLError) -- catching only OSError
    # would let this one escape and crash onboarding. This is the same class
    # of bug BOOT-D.2's *plan snippet* had -- `except OSError` around a
    # subprocess.TimeoutExpired (also not an OSError) -- which review caught
    # before it shipped; BOOT-D.2 itself never shipped with that bug.
    def url_open(_url: str, timeout: float = 0.0) -> FakeResponse:
        raise http.client.BadStatusLine("garbage")

    assert onboarding.zotero_running(url_open=url_open) is False


def test_zotero_probe_is_false_on_malformed_status_value_error() -> None:
    def url_open(_url: str, timeout: float = 0.0) -> MalformedStatusResponse:
        return MalformedStatusResponse()

    assert onboarding.zotero_running(url_open=url_open) is False


class NonNumericStatusResponse:
    """A response whose ``status`` cannot be coerced to ``int`` via ``TypeError``.

    ``int([])``/``int({})``/``int(object())`` raise ``TypeError``, a distinct
    failure mode from ``MalformedStatusResponse``'s ``ValueError``. Only
    reachable via an injected fake -- the production default's ``urlopen``
    response never returns a non-numeric ``status`` -- but the function's own
    "must never raise" contract does not carve out an exception for it.
    """

    status = object()

    def __enter__(self) -> NonNumericStatusResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


def test_zotero_probe_is_false_on_non_numeric_status_type_error() -> None:
    def url_open(_url: str, timeout: float = 0.0) -> NonNumericStatusResponse:
        return NonNumericStatusResponse()

    assert onboarding.zotero_running(url_open=url_open) is False


def test_zotero_probe_default_opener_is_the_hardened_opener() -> None:
    # Regression guard: a future edit reverting the default back to bare
    # urllib.request.urlopen would not fail any of the tests above, since
    # they all inject their own fake. Pin the default explicitly.
    default = inspect.signature(onboarding.zotero_running).parameters["url_open"].default
    assert default is onboarding._open_zotero_probe


def test_zotero_probe_default_opener_ignores_ambient_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    # urllib.request.urlopen honors http_proxy/https_proxy even for a
    # 127.0.0.1 target (urllib.request.proxy_bypass does not exempt
    # loopback), so under a corporate/dev-container proxy the probe would
    # leave the machine. Prove the default opener instead reaches the real
    # loopback target directly and never touches the configured proxy.
    target_seen = threading.Event()

    class TargetHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            target_seen.set()
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_args: object) -> None:
            return

    target_server = ThreadingHTTPServer(("127.0.0.1", 0), TargetHandler)
    target_port = int(target_server.server_address[1])
    target_thread = threading.Thread(target=target_server.serve_forever, daemon=True)
    target_thread.start()

    proxy_seen = threading.Event()

    class ProxyStubHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            proxy_seen.set()
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_args: object) -> None:
            return

    proxy_server = ThreadingHTTPServer(("127.0.0.1", 0), ProxyStubHandler)
    proxy_port = int(proxy_server.server_address[1])
    proxy_thread = threading.Thread(target=proxy_server.serve_forever, daemon=True)
    proxy_thread.start()

    monkeypatch.setenv("http_proxy", f"http://127.0.0.1:{proxy_port}")
    monkeypatch.delenv("no_proxy", raising=False)
    # getproxies_environment() honours both cases. Without clearing the uppercase
    # form this guard goes vacuous under NO_PROXY=localhost,127.0.0.1 — which
    # corporate and dev-container images set by default, i.e. exactly the
    # environments the ProxyHandler({}) fix exists for.
    monkeypatch.delenv("NO_PROXY", raising=False)
    try:
        with onboarding._open_zotero_probe(
            f"http://127.0.0.1:{target_port}/connector/ping", timeout=2.0
        ) as response:
            assert response.status == 200
        assert target_seen.is_set()
        assert not proxy_seen.is_set()
    finally:
        target_server.shutdown()
        target_thread.join(timeout=5)
        target_server.server_close()
        proxy_server.shutdown()
        proxy_thread.join(timeout=5)
        proxy_server.server_close()


def _fake_zotero(detected: bool):
    def url_open(_url: str, timeout: float = 0.0) -> FakeResponse:
        if not detected:
            raise OSError("connection refused")
        return FakeResponse(200)

    return url_open


def _linux_home_with_obsidian(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    entry = home / ".local/share/applications/obsidian.desktop"
    entry.parent.mkdir(parents=True)
    entry.write_text("[Desktop Entry]\n", encoding="utf-8")
    return home


def test_run_onboarding_full_runway_with_zotero_detected(tmp_path: Path) -> None:
    workspace = tmp_path / "vault"
    workspace.mkdir()
    (workspace / "Start here.md").write_text("# Start here\n", encoding="utf-8")
    home = _linux_home_with_obsidian(tmp_path)
    run = FakeRun(returncode=0)
    said: list[str] = []

    payload = onboarding.run_onboarding(
        workspace,
        sys_platform="linux",
        env={},
        home=home,
        ask=lambda _prompt: "",
        say=said.append,
        run=run,
        url_open=_fake_zotero(True),
    )

    statuses = {step["step"]: step["status"] for step in payload["steps"]}
    assert payload["ok"] is True
    assert payload["completed"] is True
    assert payload["workspace"] == str(workspace)
    assert statuses == {
        "obsidian": "present",
        "open-vault": "opened",
        "zotero": "offered",
        "credentials": "noticed",
    }
    assert any(onboarding.ZOTERO_HOWTO_URL in line for line in said)
    assert onboarding.CREDENTIALS_NOTICE in said


def test_run_onboarding_declined_install_skips_open_and_stays_honest(tmp_path: Path) -> None:
    workspace = tmp_path / "vault"
    workspace.mkdir()
    said: list[str] = []

    payload = onboarding.run_onboarding(
        workspace,
        sys_platform="linux",
        env={"XDG_DATA_HOME": str(tmp_path / "empty"), "XDG_DATA_DIRS": str(tmp_path / "none")},
        home=tmp_path / "home",
        ask=lambda _prompt: "n",
        say=said.append,
        run=FakeRun(returncode=1),
        url_open=_fake_zotero(False),
    )

    statuses = {step["step"]: step["status"] for step in payload["steps"]}
    assert payload["ok"] is True
    assert payload["completed"] is False
    assert statuses == {
        "obsidian": "declined",
        "open-vault": "skipped",
        "zotero": "not-detected",
        "credentials": "noticed",
    }
    assert onboarding.MANUAL_OPEN_FALLBACK.format(path=workspace) in said
    assert onboarding.CREDENTIALS_NOTICE in said


def test_run_onboarding_install_failure_is_reported_and_open_is_skipped(tmp_path: Path) -> None:
    # Proves the "failed" obsidian status (distinct from "declined"/"manual")
    # is actually reachable through the orchestrator, and that a failed
    # install still skips the open-vault step rather than attempting it.
    workspace = tmp_path / "vault"
    workspace.mkdir()
    said: list[str] = []

    payload = onboarding.run_onboarding(
        workspace,
        sys_platform="linux",
        env={"XDG_DATA_HOME": str(tmp_path / "empty"), "XDG_DATA_DIRS": str(tmp_path / "none")},
        home=tmp_path / "home",
        ask=lambda _prompt: "y",
        say=said.append,
        run=FakeRun(returncode=1),
        url_open=_fake_zotero(False),
    )

    statuses = {step["step"]: step["status"] for step in payload["steps"]}
    assert payload["ok"] is True
    assert payload["completed"] is False
    assert statuses["obsidian"] == "failed"
    assert statuses["open-vault"] == "skipped"


def test_run_onboarding_open_vault_failure_leaves_incomplete_even_when_obsidian_present(
    tmp_path: Path,
) -> None:
    # Proves the "manual" open-vault status is reachable even when Obsidian
    # is already present, and that `completed` correctly stays False: both
    # legs of the AND (obsidian present/installed, vault opened) must hold.
    workspace = tmp_path / "vault"
    workspace.mkdir()
    home = _linux_home_with_obsidian(tmp_path)
    said: list[str] = []

    payload = onboarding.run_onboarding(
        workspace,
        sys_platform="linux",
        env={},
        home=home,
        ask=lambda _prompt: "",
        say=said.append,
        run=FakeRun(returncode=1),
        url_open=_fake_zotero(False),
    )

    statuses = {step["step"]: step["status"] for step in payload["steps"]}
    assert payload["ok"] is True
    assert payload["completed"] is False
    assert statuses["obsidian"] == "present"
    assert statuses["open-vault"] == "manual"
    assert onboarding.MANUAL_OPEN_FALLBACK.format(path=workspace) in said


def test_run_onboarding_ask_failure_is_treated_as_declined_not_a_crash(tmp_path: Path) -> None:
    # `ask` is not total: builtin input() raises RuntimeError("input(): lost
    # sys.stdin"), not EOFError, when stdin is closed/detached, and
    # offer_obsidian_install only guards its own ask() call against EOFError.
    # The orchestrator must not let this escape and crash the whole
    # onboarding sequence -- an unreadable prompt is an honest "no consent"
    # outcome, not a failure.
    workspace = tmp_path / "vault"
    workspace.mkdir()
    said: list[str] = []

    def ask(_prompt: str) -> str:
        raise RuntimeError("input(): lost sys.stdin")

    payload = onboarding.run_onboarding(
        workspace,
        sys_platform="linux",
        env={"XDG_DATA_HOME": str(tmp_path / "empty"), "XDG_DATA_DIRS": str(tmp_path / "none")},
        home=tmp_path / "home",
        ask=ask,
        say=said.append,
        run=FakeRun(returncode=1),
        url_open=_fake_zotero(False),
    )

    statuses = {step["step"]: step["status"] for step in payload["steps"]}
    assert payload["ok"] is True
    assert payload["completed"] is False
    assert statuses["obsidian"] == "declined"
    assert statuses["open-vault"] == "skipped"
    assert any(onboarding.OBSIDIAN_DOWNLOAD_URL in line for line in said)


def test_run_onboarding_default_zotero_opener_is_the_hardened_opener() -> None:
    # Regression guard: the plan's BOOT-D.5 snippet listed a stale
    # `urllib.request.urlopen` default for `url_open`, which -- since
    # run_onboarding always forwards `url_open` explicitly to
    # zotero_running -- would silently undo BOOT-D.4's proxy-free,
    # redirect-free hardening whenever a caller (e.g. the future `memoria
    # onboard` CLI) does not pass its own `url_open`. Pin the default
    # explicitly, mirroring zotero_running's own regression guard.
    default = inspect.signature(onboarding.run_onboarding).parameters["url_open"].default
    assert default is onboarding._open_zotero_probe


def test_zotero_probe_default_opener_does_not_follow_redirects() -> None:
    # An unhardened opener follows a 301/302/303/307/308 -- including to an
    # ftp:// target, whose addinfourl has status None, which this probe
    # would otherwise treat as success. Prove the default opener raises
    # instead of following, and never reaches the redirect target.
    target_seen = threading.Event()

    class TargetHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            target_seen.set()
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_args: object) -> None:
            return

    target_server = ThreadingHTTPServer(("127.0.0.1", 0), TargetHandler)
    target_port = int(target_server.server_address[1])
    target_thread = threading.Thread(target=target_server.serve_forever, daemon=True)
    target_thread.start()

    class RedirectHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{target_port}/connector/ping")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_args: object) -> None:
            return

    redirect_server = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
    redirect_port = int(redirect_server.server_address[1])
    redirect_thread = threading.Thread(target=redirect_server.serve_forever, daemon=True)
    redirect_thread.start()
    try:
        with pytest.raises(urllib.error.HTTPError):
            onboarding._open_zotero_probe(
                f"http://127.0.0.1:{redirect_port}/connector/ping", timeout=2.0
            )
        assert not target_seen.is_set()
    finally:
        redirect_server.shutdown()
        redirect_thread.join(timeout=5)
        redirect_server.server_close()
        target_server.shutdown()
        target_thread.join(timeout=5)
        target_server.server_close()
