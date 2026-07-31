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
