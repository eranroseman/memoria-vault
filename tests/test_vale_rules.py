"""Pin the curated Vale rule set and offline-vendoring invariant.

Vale enforces terminology and usage over published docs prose. The rules are
chosen individually rather than by adopting a package: measured 2026-08,
adopting Microsoft and Google together triple-counted the same sentence, and
93% of the combined error tier was house-style rules contradicting this repo's
own conventions.

A rule dropped from .vale.ini leaves the gate green and silent, the same shape
as a `files:` regex that matches nothing. This test makes that loud.
"""

from __future__ import annotations

import configparser

import pytest

from tests.paths import ROOT

pytestmark = pytest.mark.static

VALE_INI = ROOT / ".vale.ini"
STYLES = ROOT / ".vale/styles"

# The nine rules admitted after measuring the current documentation corpus.
REQUIRED_RULES = {
    "Microsoft.Avoid",
    "Microsoft.Quotes",
    "Microsoft.Jargon",
    "Microsoft.HeadingPunctuation",
    "Microsoft.UIVerbs",
    "alex.Condescending",
    "alex.Race",
    "write-good.ThereIs",
    "write-good.So",
}

VENDORED_PACKAGES = ("Microsoft", "alex", "write-good")


def _parsed() -> configparser.ConfigParser:
    """Read Vale's preamble and sectioned config with the standard parser."""
    parser = configparser.ConfigParser(allow_no_value=True, delimiters=("=",))
    parser.optionxform = str  # Vale rule names are case-sensitive.
    parser.read_string("[global]\n" + VALE_INI.read_text(encoding="utf-8"))
    return parser


def _markdown_section() -> dict[str, str]:
    return dict(_parsed()["*.md"])


def _setting_value(value: str) -> str:
    return value.split(";", maxsplit=1)[0].strip()


def _enabled_rule_names() -> set[str]:
    """Return error-level style rules, excluding non-rule Vale settings."""
    return {
        name
        for name, value in _markdown_section().items()
        if "." in name and _setting_value(value) == "error"
    }


def test_exactly_the_curated_rules_are_enabled_at_error():
    """Catch a rejected candidate entering, or an admitted rule leaving, the gate."""
    assert _enabled_rule_names() == REQUIRED_RULES, (
        "the error-level Vale rules must be exactly the curated set; "
        f"got {sorted(_enabled_rule_names())}"
    )


def test_spelling_stays_with_cspell():
    assert _setting_value(_markdown_section().get("Vale.Spelling", "")) == "NO", (
        "Vale must not spell-check; cspell owns spelling (CONTRIBUTING, Spelling)"
    )


def test_styles_are_vendored_so_the_gate_runs_offline():
    """`vale sync` is a manual refresh; the hook only runs `vale`."""
    global_settings = _parsed()["global"]
    configured_styles = _setting_value(global_settings.get("StylesPath", ""))
    assert configured_styles == ".vale/styles"
    assert ROOT / configured_styles == STYLES
    packages = tuple(
        package.strip()
        for package in _setting_value(global_settings.get("Packages", "")).split(",")
    )
    assert packages == VENDORED_PACKAGES
    for package in VENDORED_PACKAGES:
        directory = STYLES / package
        assert directory.is_dir(), (
            f"{directory} is missing; run `vale sync` and commit it. The gate has no network."
        )
        assert (directory / "meta.json").is_file(), (
            f"{directory}/meta.json is missing, so the vendored version cannot be audited"
        )


def test_min_alert_level_is_error():
    level = _parsed()["global"].get("MinAlertLevel", "")
    assert _setting_value(level) == "error", (
        "MinAlertLevel must stay at error; lowering it turns every rule in "
        "REQUIRED_RULES into a warning the gate ignores"
    )
