"""The tutorial sample vault is a bundled, labeled, removable install asset."""

import re
from pathlib import Path

import yaml

SRC = Path(__file__).resolve().parent.parent / "src"
ROOT = SRC.parent
SAMPLE = SRC / ".memoria" / "samples" / "mediterranean-diet"
SCRIPTS = SRC / "system" / "scripts"


def _frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    assert match, f"{path}: missing YAML frontmatter"
    return match.group(1)


def test_sample_vault_is_bundled_under_src_not_repo_root():
    assert not (ROOT / "sample-vault").exists()
    assert SAMPLE.is_dir()
    assert (SAMPLE / "catalog" / "papers").is_dir()
    assert (SAMPLE / "notes" / "claims").is_dir()
    assert (SAMPLE / "notes" / "hubs").is_dir()
    assert (SAMPLE / "notes" / "sources").is_dir()


def test_every_sample_note_is_labeled_and_loadable():
    notes = sorted(SAMPLE.rglob("*.md"))
    assert len(notes) == 34
    assert len(sorted((SAMPLE / "catalog" / "papers").glob("*.md"))) == 10
    assert len(sorted((SAMPLE / "notes" / "sources").glob("*.md"))) == 10
    for path in notes:
        rel = path.relative_to(SAMPLE).as_posix()
        assert rel.startswith(("catalog/", "notes/")), rel
        text = path.read_text(encoding="utf-8")
        fm = _frontmatter(path)
        assert re.search(r"^sample:\s*true$", fm, re.M), path
        assert not re.search(r"\[\[[^\]|#]+\]\]", text), path


def test_sample_sources_meet_full_map_floor():
    calibration = yaml.safe_load((SRC / ".memoria" / "schemas" / "calibration.yaml").read_text())
    required = calibration["clustering"]["full_cluster_min_documents"]
    sources = sorted((SAMPLE / "notes" / "sources").glob("*.md"))
    non_empty = 0
    for path in sources:
        text = path.read_text(encoding="utf-8")
        body = re.sub(r"^---\n(.*?)\n---", "", text, count=1, flags=re.S)
        if body.strip():
            non_empty += 1
    assert non_empty >= required


def test_sample_commands_are_narrow_and_offline_bundled():
    load = (SCRIPTS / "load-sample-vault.js").read_text(encoding="utf-8")
    remove = (SCRIPTS / "remove-sample-vault.js").read_text(encoding="utf-8")

    for marker in (
        'SAMPLE_ROOT = ".memoria/samples/mediterranean-diet"',
        'LIVE_PREFIXES = ["catalog/", "notes/"]',
        'fs.readFileSync(sourcePath, "utf8")',
        "if (await exists(adapter, rel))",
        "await adapter.write(rel,",
    ):
        assert marker in load
    assert "fetch(" not in load

    for marker in (
        'LIVE_PREFIXES = ["catalog/", "notes/"]',
        "hasSampleTrue(text)",
        'fm.lifecycle = "archived"',
        "fm.archived = today",
        "sample:\\s*true",
    ):
        assert marker in remove
    assert "app.vault.delete" not in remove
    assert "app.vault.trash" not in remove
