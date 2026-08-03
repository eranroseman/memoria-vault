"""Only the standalone Obsidian proof-adapter package is allowed."""

from pathlib import Path

import pytest

from scripts.checks import plugin_provenance_doctor as doctor
from tests.paths import ROOT

pytestmark = pytest.mark.static


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


def test_plugin_scope_doctor_flags_a_foreign_plugin_directory(tmp_path):
    """A second plugin dropped into the seeded .obsidian tree is refused wholesale.

    The retired-payload denylist that used to be asserted here moved to
    removed_surfaces.json; tests/test_removed_surface_gate.py now pins it.
    What stays is this doctor's own job: nothing ships under the seed's
    .obsidian tree unless the allowlist names it, foreign plugin dirs included.
    """
    root = tmp_path / "repo"
    (root / "src/memoria_vault/product/workspace_seed/.obsidian/plugins/extra").mkdir(parents=True)
    (
        root / "src/memoria_vault/product/workspace_seed/.obsidian/plugins/extra/manifest.json"
    ).write_text("{}", encoding="utf-8")

    findings = doctor.check(root)

    assert [finding.split(":", 1)[0] for finding in findings] == [
        "src/memoria_vault/product/workspace_seed/.obsidian/plugins/extra/manifest.json"
    ]
