"""Every tracked authored file is claimed by a gate, or declared unclaimed with a reason.

Scope has escaped four times on record and once more when this test was written:
`scripts/verify` was the one Python file exempt from both ruff hooks;
`scripts/dev/setup.sh` was covered by no gate at all; an alternation in the
shellcheck hook named `scripts/install/`, deleted in #1322, so it matched
nothing and stayed green; `.claude/hooks/block-git-add-all.py` sits outside
every scope; and the seeded `.githooks/pre-commit` is a bash script shipped to
every vault that shellcheck's `^scripts/` scope does not reach.

Each was fixed on its own and memorialised as a comment. None of those comments
can fail. This test computes the claimed set instead, in the spirit of
`test_policy_gate_completeness.py`: a boundary test must prove the boundary is
complete, not that one known case is handled.

It reads the tool configs rather than restating them. The per-type mapping below
does re-encode "what counts as Python", which the hook comments say was
abandoned for `files:` regexes — the difference is failure mode. A stale filter
fails silent (green hook, nothing linted); a stale test fails loud, naming the
file.
"""

from __future__ import annotations

import inspect
import json
import os
import re
import runpy
import shutil
import subprocess

import pytest
import yaml

from tests.paths import ROOT

pytestmark = pytest.mark.static

PRECOMMIT = ROOT / ".pre-commit-config.yaml"
CSPELL = ROOT / "cspell.json"

# Every extension tracked in this repo, mapped to the gate that claims it.
# A new extension fails `test_every_tracked_extension_has_a_policy` until it is
# added here, which is the point: a new language must be a decision, not a drift.
KNOWN_EXTENSIONS: dict[str, str] = {
    ".py": "ruff",
    ".sh": "shellcheck",
    ".ps1": "psscriptanalyzer",
    ".js": "oxlint",
    ".mjs": "oxlint",
    ".yaml": "yamllint",
    ".yml": "yamllint",
    ".json": "check_json",
    ".md": "cspell",
    # Claimed by no linter, on purpose. The reason is the value.
    ".toml": "unclaimed: pyproject.toml and mise.toml are parsed by their consumers",
    ".css": "unclaimed: 2 files, one a generated bundle; three CSS files is not a mechanism",
    ".scss": "unclaimed: 1 Jekyll theme override",
    ".base": "unclaimed: Obsidian Bases config, shipped as package data",
    ".sql": "unclaimed: runtime package data, exercised by the migration tests",
    ".bib": "unclaimed: generated bibliography artifact",
    ".txt": "unclaimed: project word vocabulary and requirements-dev dependency pins",
    ".cff": "unclaimed: citation metadata",
    ".ini": "unclaimed: .vale.ini, read by the vale hook itself",
    ".psd1": "unclaimed: PSScriptAnalyzer settings, read by the analyzer itself",
    ".ico": "unclaimed: binary",
    ".gitignore": "unclaimed: git metadata",
    ".gitattributes": "unclaimed: git metadata",
    # Basename contains a dot, so the extension derivation below sees the whole
    # tail as the extension. It belongs here rather than in EXTENSIONLESS.
    ".git-blame-ignore-revs": "unclaimed: git metadata",
    ".yamllint": "unclaimed: yamllint's own config, read by the hook",
}

# Files of a claimed type that no gate reaches, each with the reason it is exempt.
# An entry here is a decision on the record, not an oversight.
UNCLAIMED: dict[str, str] = {
    "src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/main.js": (
        "generated esbuild bundle; `npm run check --prefix packages/memoria-obsidian` "
        "compares it byte-for-byte against a fresh build, so formatting it fails that check"
    ),
    "docs/reference/evidence-and-integrations/bibliography.md": (
        "cited-source metadata with proper names and titles"
    ),
    "docs/superpowers/**": "tracked point-in-time working specs and plans, not published docs",
    "design-history/archive/**": "frozen historical record",
}

# Tracked files with no extension at all, and what claims each.
EXTENSIONLESS: dict[str, str] = {
    "scripts/verify": "ruff",
    "src/memoria_vault/product/workspace_seed/.githooks/pre-commit": "shellcheck",
    "LICENSE": "unclaimed: license text",
}


def _tracked() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.splitlines()


def _hook(hook_id: str) -> dict:
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = [h for repo in config["repos"] for h in repo["hooks"] if h["id"] == hook_id]
    assert len(hooks) == 1, f"expected exactly one {hook_id} hook, got {len(hooks)}"
    return hooks[0]


def _positive_glob_matches(path: str, pattern: str, *, enable_glob_dot: bool) -> bool:
    """Match CSpell's current positive glob subset: `*`, `**`, and `?`."""
    pieces = ["^"]
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "*":
            if index + 1 < len(pattern) and pattern[index + 1] == "*":
                if index + 2 < len(pattern) and pattern[index + 2] == "/":
                    pieces.append("(?:.*/)?")
                    index += 3
                else:
                    pieces.append(".*")
                    index += 2
            else:
                pieces.append("[^/]*")
                index += 1
        elif char == "?":
            pieces.append("[^/]")
            index += 1
        else:
            pieces.append(re.escape(char))
            index += 1
    pieces.append("$")
    if not enable_glob_dot and any(part.startswith(".") for part in path.split("/")):
        return False
    return re.match("".join(pieces), path) is not None


def _unclaimed_reason(path: str) -> str | None:
    """Return the explicit exemption reason for a path, if one exists."""
    return next(
        (
            reason
            for pattern, reason in UNCLAIMED.items()
            if _positive_glob_matches(path, pattern, enable_glob_dot=True)
        ),
        None,
    )


def _cspell_claims(path: str) -> bool:
    config = json.loads(CSPELL.read_text(encoding="utf-8"))
    enable_glob_dot = config.get("enableGlobDot", False)
    selected = any(
        _positive_glob_matches(path, pattern, enable_glob_dot=enable_glob_dot)
        for pattern in config["files"]
    )
    ignored = any(
        _positive_glob_matches(path, pattern, enable_glob_dot=enable_glob_dot)
        for pattern in config.get("ignorePaths", [])
    )
    return selected and not ignored


def _claims(hook_id: str, path: str) -> bool:
    """True when the hook's own `files`/`exclude` scope reaches `path`."""
    hook = _hook(hook_id)
    if not re.search(hook["files"], path):
        return False
    exclude = hook.get("exclude")
    if exclude and re.search(exclude, path):
        return False
    return hook_id != "cspell" or _cspell_claims(path)


# Which hook id enforces each claimed extension. `.json` and `.ps1` are claimed
# by native gates in `scripts/verify`, not by a pre-commit hook, so they are
# handled separately below.
HOOK_FOR_OWNER = {
    "ruff": "ruff",
    "shellcheck": "shellcheck",
    "oxlint": "oxlint",
    "yamllint": "yamllint",
    "cspell": "cspell",
}

NATIVE_OWNERS = {"check_json", "psscriptanalyzer"}
KNOWN_OWNERS = set(HOOK_FOR_OWNER) | NATIVE_OWNERS
POLICY_MAPS = {
    "KNOWN_EXTENSIONS": KNOWN_EXTENSIONS,
    "EXTENSIONLESS": EXTENSIONLESS,
}


def _policy_error(policy: str) -> str | None:
    """Return why a policy value is invalid, if it is not an intentional owner."""
    if policy in KNOWN_OWNERS:
        return None
    if policy.startswith("unclaimed:") and policy.removeprefix("unclaimed:").strip():
        return None
    return (
        f"{policy!r} is not a known owner ({', '.join(sorted(KNOWN_OWNERS))}) "
        "or 'unclaimed: <reason>'"
    )


def _validate_policies() -> list[str]:
    """Validate policy maps rather than trusting their values as test configuration."""
    invalid = [
        f"KNOWN_EXTENSIONS[{extension!r}]: {_policy_error(owner)}"
        for extension, owner in KNOWN_EXTENSIONS.items()
        if _policy_error(owner) is not None
    ]
    invalid.extend(
        f"EXTENSIONLESS[{path!r}]: {_policy_error(owner)}"
        for path, owner in EXTENSIONLESS.items()
        if _policy_error(owner) is not None
    )
    invalid.extend(
        f"UNCLAIMED[{pattern!r}] needs a nonempty reason"
        for pattern, reason in UNCLAIMED.items()
        if not isinstance(reason, str) or not reason.strip()
    )
    return invalid


def test_policy_values_name_a_known_owner_or_reasoned_exemption() -> None:
    assert _validate_policies() == []


@pytest.mark.parametrize(
    ("mapping_name", "key", "policy"),
    [
        ("KNOWN_EXTENSIONS", ".py", "ruf"),
        ("KNOWN_EXTENSIONS", ".txt", "unclaimed:"),
        ("EXTENSIONLESS", "scripts/verify", "verify"),
        ("EXTENSIONLESS", "LICENSE", "unclaimed:   "),
    ],
)
def test_invalid_policy_values_are_rejected(
    monkeypatch: pytest.MonkeyPatch, mapping_name: str, key: str, policy: str
) -> None:
    mapping = POLICY_MAPS[mapping_name]
    monkeypatch.setitem(mapping, key, policy)
    errors = _validate_policies()
    assert len(errors) == 1
    assert key in errors[0]
    assert policy in errors[0]


def test_blank_unclaimed_reason_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(UNCLAIMED, "docs/superpowers/**", "   ")
    assert _validate_policies() == ["UNCLAIMED['docs/superpowers/**'] needs a nonempty reason"]


def test_every_tracked_extension_has_a_policy():
    """A new file type must be a decision. Add it to KNOWN_EXTENSIONS."""
    seen = {"." + name.rsplit(".", 1)[1] for name in _tracked() if "." in name.rsplit("/", 1)[-1]}
    undeclared = sorted(seen - set(KNOWN_EXTENSIONS))
    assert undeclared == [], (
        f"tracked extensions with no declared owner: {undeclared}. "
        "Add each to KNOWN_EXTENSIONS with an owner or an 'unclaimed: <reason>' string."
    )


def test_every_extensionless_tracked_file_has_a_policy():
    undeclared = sorted(
        name
        for name in _tracked()
        if "." not in name.rsplit("/", 1)[-1] and name not in EXTENSIONLESS
    )
    assert undeclared == [], (
        f"tracked files with no extension and no declared owner: {undeclared}. "
        "Add each to EXTENSIONLESS."
    )


def test_every_unclaimed_glob_matches_a_tracked_file():
    for pattern in UNCLAIMED:
        assert any(
            _positive_glob_matches(path, pattern, enable_glob_dot=True) for path in _tracked()
        ), f"unclaimed glob matches no tracked file: {pattern}"


def test_every_cspell_ignored_markdown_file_has_an_unclaimed_reason():
    config = json.loads(CSPELL.read_text(encoding="utf-8"))
    enable_glob_dot = config.get("enableGlobDot", False)
    ignored = [
        path
        for path in _tracked()
        if path.endswith(".md")
        and any(
            _positive_glob_matches(path, pattern, enable_glob_dot=enable_glob_dot)
            for pattern in config.get("ignorePaths", [])
        )
    ]
    missing_reason = sorted(path for path in ignored if _unclaimed_reason(path) is None)
    assert missing_reason == [], (
        f"CSpell-ignored Markdown must have a narrow unclaimed reason: {missing_reason}"
    )


@pytest.mark.parametrize("owner", sorted(HOOK_FOR_OWNER))
def test_claimed_files_fall_inside_their_owner_scope(owner: str):
    extensions = [ext for ext, who in KNOWN_EXTENSIONS.items() if who == owner]
    paths = [
        name
        for name in _tracked()
        if any(name.endswith(ext) for ext in extensions) and _unclaimed_reason(name) is None
    ]
    paths += [name for name, who in EXTENSIONLESS.items() if who == owner]
    escaped = sorted(path for path in paths if not _claims(HOOK_FOR_OWNER[owner], path))
    assert escaped == [], (
        f"tracked files the {owner} hook's `files` scope does not reach: {escaped}. "
        "Either widen the hook scope in .pre-commit-config.yaml or add the file to "
        "UNCLAIMED with the reason it is exempt."
    )


def test_json_and_powershell_are_claimed_by_the_verify_roster():
    """Native JSON and PowerShell checks enumerate tracked files from Git."""
    namespace = runpy.run_path(str(ROOT / "scripts/verify"), run_name="_verify_probe")
    check_json = namespace["check_json"]
    check_powershell = namespace["check_powershell"]
    pssa_command = namespace["PSSA_COMMAND"]
    extra_steps = namespace["EXTRA_STEPS"]
    shards = namespace["SHARDS"]

    assert '["git", "ls-files", "*.json"]' in inspect.getsource(check_json), (
        "check_json must enumerate tracked JSON from git, not a hardcoded list"
    )
    assert set(extra_steps) <= set(shards), "EXTRA_STEPS names shards SHARDS does not declare"
    assert check_json in extra_steps["lint"]
    assert check_powershell in extra_steps["lint"]

    if shutil.which("pwsh") is None:
        pytest.skip("pwsh not installed; check_powershell() would self-skip too")

    harness = r"""
function Get-Module {
    param([switch] $ListAvailable, [string] $Name)
    [pscustomobject]@{ Name = "PSScriptAnalyzer" }
}
$script:gitInvocations = @()
function git {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]] $Arguments)
    $script:gitInvocations += ,@($Arguments)
    if ($Arguments.Count -ne 2 -or $Arguments[0] -ne "ls-files" -or $Arguments[1] -ne "*.ps1") {
        throw "expected git ls-files '*.ps1'"
    }
    "fixtures/first.ps1"
    "fixtures/second.ps1"
}
$script:capturedPaths = @()
function Invoke-ScriptAnalyzer {
    param([Parameter(Mandatory = $true)][string[]] $Path, [string[]] $Severity, [string] $Settings)
    $script:capturedPaths = @($Path)
    return $null
}
& ([scriptblock]::Create($env:PSSA_COMMAND))
[pscustomobject]@{
    gitInvocations = @($script:gitInvocations)
    capturedPaths = @($script:capturedPaths)
} | ConvertTo-Json -Compress -Depth 4
"""
    environment = dict(os.environ)
    environment["PSSA_COMMAND"] = pssa_command
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", harness],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    captured = json.loads(result.stdout)
    assert captured["gitInvocations"] == [["ls-files", "*.ps1"]]
    assert captured["capturedPaths"] == ["fixtures/first.ps1", "fixtures/second.ps1"]
