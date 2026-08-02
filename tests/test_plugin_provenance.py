"""Only the standalone Obsidian proof-adapter package is allowed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import pytest

from scripts.checks import plugin_provenance_doctor as doctor

pytestmark = pytest.mark.static

ROOT = Path(__file__).resolve().parent.parent


def test_plugin_scope_doctor_accepts_standalone_repo():
    assert doctor.check(ROOT) == []


def test_plugin_scope_doctor_allows_memoria_obsidian_package(tmp_path):
    root = tmp_path / "repo"
    (root / "packages/memoria-obsidian").mkdir(parents=True)

    assert doctor.check(root) == []


def test_plugin_scope_doctor_allows_ring1_view_preference_files(tmp_path):
    root = tmp_path / "repo"
    obsidian = root / "src/memoria_vault/product/workspace_seed/.obsidian"
    obsidian.mkdir(parents=True)
    (obsidian / "graph.json").write_text("{}", encoding="utf-8")
    (obsidian / "types.json").write_text("{}", encoding="utf-8")

    assert doctor.check(root) == []


def test_plugin_scope_doctor_still_denies_an_unlisted_memoria_obsidian_file(tmp_path):
    """The allowlist stayed deny-by-default after U3-PLUG widened it.

    It was widened twice, from four files to eight, to let the plugin ship the
    CommonJS modules its entrypoint requires. A widening implemented as a
    prefix or glob over `plugins/memoria-obsidian/` would have passed every
    other test in this file while silently admitting anything dropped in that
    directory forever after -- which is the payload this doctor exists to
    refuse. So the seeded plugin directory is rebuilt with exactly its allowed
    files plus one interloper, and only the interloper may be reported.

    The interloper is deliberately a name no plugin module will ever take. It
    used to be `relate.js`, and U3-PLUG.5 -- the task that added `relate.js` to
    the allowlist -- turned this test's interloper into an allowed file. The
    membership assertion below is what makes that recurrence loud instead of
    vacuous.
    """
    root = tmp_path / "repo"
    seed_obsidian = root / "src/memoria_vault/product/workspace_seed/.obsidian"
    for rel in sorted(doctor.ALLOWED_SEED_OBSIDIAN_FILES):
        target = seed_obsidian / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")
    interloper_rel = Path("plugins/memoria-obsidian/not-a-bundled-module.js")
    assert interloper_rel not in doctor.ALLOWED_SEED_OBSIDIAN_FILES
    interloper = seed_obsidian / interloper_rel
    interloper.write_text("// never allowed\n", encoding="utf-8")

    findings = doctor.check(root)

    assert [finding.split(":", 1)[0] for finding in findings] == [
        "src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/"
        "not-a-bundled-module.js"
    ]
    interloper.unlink()
    assert doctor.check(root) == []


def test_plugin_scope_doctor_flags_removed_payloads(tmp_path):
    root = tmp_path / "repo"
    (root / "src/memoria_vault/product/workspace_seed/.obsidian/plugins/extra").mkdir(parents=True)
    (
        root / "src/memoria_vault/product/workspace_seed/.obsidian/plugins/extra/manifest.json"
    ).write_text("{}", encoding="utf-8")
    (root / "src/memoria_vault/product/workspace_seed/.memoria/plugins").mkdir(parents=True)
    (root / "src/memoria_vault/product/workspace_seed/system/scripts").mkdir(parents=True)
    (root / "src/.obsidian").mkdir(parents=True)
    (root / "packages/obsidian-plugin").mkdir(parents=True)
    (root / "src/memoria_vault/obsidian_adapter").mkdir(parents=True)
    (root / "src/memoria_vault/runtime/agent_client.py").parent.mkdir(parents=True)
    (root / "src/memoria_vault/runtime/agent_client.py").write_text("", encoding="utf-8")
    (root / "tests").mkdir(parents=True)
    (root / "tests/test_memoria_inspector.py").write_text("", encoding="utf-8")
    (root / "tests/test_obsidian_plugin.py").write_text("", encoding="utf-8")

    findings = doctor.check(root)

    assert {finding.split(":", 1)[0] for finding in findings} == {
        "packages/obsidian-plugin",
        "src/memoria_vault/obsidian_adapter",
        "src/memoria_vault/product/workspace_seed/.memoria/plugins",
        "src/memoria_vault/product/workspace_seed/.obsidian/plugins/extra/manifest.json",
        "src/memoria_vault/product/workspace_seed/system/scripts",
        "src/memoria_vault/runtime/agent_client.py",
        "src/.obsidian",
        "tests/test_memoria_inspector.py",
        "tests/test_obsidian_plugin.py",
    }
