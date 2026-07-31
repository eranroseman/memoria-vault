"""Onboarding runway unit tests: injected IO for every probe (bootstrap spec section 7)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from memoria_vault.runtime import onboarding


class FakeRun:
    def __init__(self, returncode: int = 0, raises: Exception | None = None) -> None:
        self.calls: list[list[str]] = []
        self.returncode = returncode
        self.raises = raises

    def __call__(self, argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
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


def test_offer_install_never_runs_a_command_outside_the_allowlist() -> None:
    # The allowlist is frozen: even if `ask` is abused to return something
    # that looks like a command, only the literal allowlisted tuple for the
    # resolved platform is ever passed to `run`.
    run = FakeRun(returncode=0)

    status = onboarding.offer_obsidian_install(
        "darwin",
        ask=lambda _prompt: "y; rm -rf /",
        say=lambda _line: None,
        run=run,
    )

    assert status == "declined"
    assert run.calls == []
