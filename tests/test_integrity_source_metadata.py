from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import capture_source as _capture_source
from memoria_vault.runtime.integrity import check_source_metadata as _check_source_metadata
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import call_with_context, copy_memoria_dirs, git, init_git


def capture_source(vault: Path, *args, **kwargs):
    return call_with_context(_capture_source, vault, *args, **kwargs)


def check_source_metadata(vault: Path, *args, **kwargs):
    return call_with_context(_check_source_metadata, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "integrity@example.invalid", "Integrity")
    return tmp_path


def sync_file_verdicts(vault: Path) -> None:
    for root in (
        "catalog",
        "knowledge",
        "notes",
        "hubs",
        "projects",
        "digests",
        "fulltext",
    ):
        base = vault / root
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            fm = read_frontmatter(path)
            status = fm.get("check_status")
            if status not in state.CHECK_STATUSES:
                continue
            if fm.get("type") == "source":
                continue
            rel = path.relative_to(vault).as_posix()
            state.record_observed_file_edit(
                vault,
                output_id=rel,
                concept_type=str(fm.get("type") or "note"),
                output_sha256=sha256_file(path),
            )
            state.set_concept_verdict(vault, rel, str(status))


def test_source_metadata_check_flags_incomplete_checked_source(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    state.upsert_catalog_record(
        vault,
        work_id="bad",
        title="Bad Metadata",
        description="Missing citekey.",
        resource="https://example.test/bad",
        citekey="",
        csl_json={
            "title": "Bad Metadata",
            "author": [{"family": "Ada", "given": "River"}],
            "issued": {"date-parts": [[2026]]},
        },
        provider_coverage="partial",
        text_status="full-text",
        check_status="checked",
    )

    sync_file_verdicts(vault)
    result = check_source_metadata(vault, shadow=False, machine="integrity-machine")

    [finding] = result["findings"]
    assert finding["check"] == "source-metadata"
    assert finding["target_id"] == "catalog/sources/bad"
    assert finding["reason"] == "missing citekey alias"
    assert finding["route"] == "ask"
    assert not (vault / "catalog/sources/bad/source.md").exists()


def test_source_metadata_check_flags_conflicting_doi(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    state.upsert_catalog_record(
        vault,
        work_id="conflict",
        title="Conflicting DOI",
        description="Mismatched identifier metadata.",
        citekey="conflict2026",
        identifiers={"doi": "10.1000/top-level"},
        csl_json={
            "title": "Conflicting DOI",
            "DOI": "https://doi.org/10.1000/csl",
            "author": [{"family": "Ada", "given": "River"}],
            "issued": {"date-parts": [[2026]]},
        },
        provider_coverage="partial",
        text_status="full-text",
        check_status="checked",
    )

    sync_file_verdicts(vault)
    result = check_source_metadata(vault, shadow=False, machine="integrity-machine")

    [finding] = result["findings"]
    assert finding["check"] == "source-metadata"
    assert finding["target_id"] == "catalog/sources/conflict"
    assert finding["reason"] == "conflicting DOI metadata"
    assert finding["route"] == "ask"
    assert not (vault / "catalog/sources/conflict/source.md").exists()


def test_source_metadata_check_routes_duplicate_source_external_ids_to_attention(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    state.upsert_catalog_record(
        vault,
        work_id="source-one",
        title="First External ID Source",
        description="A fixture source.",
        resource="https://doi.org/10.1000/external.one",
        identifiers={"doi": "10.1000/external.one"},
        citekey="externalOne2026",
        csl_json={
            "id": "externalOne2026",
            "type": "article-journal",
            "title": "First External ID Source",
            "DOI": "10.1000/external.one",
            "issued": {"date-parts": [[2026]]},
            "author": [{"family": "River", "given": "Ada"}],
        },
        provider_coverage="full",
        text_status="full-text",
        check_status="checked",
    )
    state.upsert_catalog_record(
        vault,
        work_id="source-two",
        title="Second External ID Source",
        description="A fixture source.",
        resource="https://doi.org/10.1000/external.two",
        identifiers={"doi": "10.1000/external.two"},
        citekey="externalTwo2026",
        csl_json={
            "id": "externalTwo2026",
            "type": "article-journal",
            "title": "Second External ID Source",
            "DOI": "10.1000/external.two",
            "issued": {"date-parts": [[2026]]},
            "author": [{"family": "River", "given": "Ada"}],
        },
        provider_coverage="full",
        text_status="full-text",
        check_status="checked",
    )
    state.replace_external_ids(
        vault,
        [
            {
                "owner_type": "source",
                "owner_id": "source-one",
                "namespace": "openalex",
                "value": "https://openalex.org/W123",
            },
            {
                "owner_type": "source",
                "owner_id": "source-two",
                "namespace": "openalex",
                "value": "https://openalex.org/W123",
            },
        ],
    )

    result = check_source_metadata(
        vault,
        shadow=False,
        machine="integrity-machine",
        commit=True,
    )

    assert [
        (finding["check"], finding["target_id"], finding["reason"], finding["route"])
        for finding in result["findings"]
    ] == [
        (
            "record-linkage",
            "catalog/sources/source-one",
            "duplicate source external id openalex=https://openalex.org/W123 also used by "
            "catalog/sources/source-two",
            "ask",
        ),
        (
            "record-linkage",
            "catalog/sources/source-two",
            "duplicate source external id openalex=https://openalex.org/W123 also used by "
            "catalog/sources/source-one",
            "ask",
        ),
    ]
    assert result["attention_path"] == "inbox/work-prompt-record-linkage-source-external-ids.md"
    card = read_frontmatter(vault / result["attention_path"])
    assert card["attention_kind"] == "work-prompt"
    assert card["attention_status"] == "open"
    assert card["target"] == "catalog/sources"
    assert not (vault / "catalog/sources/source-one/source.md").exists()
    assert not (vault / "catalog/sources/source-two/source.md").exists()
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, result["attention_path"]}


def test_source_metadata_check_routes_string_block_duplicates_to_attention(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    for work_id, title, doi in (
        ("source-one", "Neural Retrieval in Memory Systems", "10.1000/block.one"),
        ("source-two", "Neural retrieval in memory systems!", "10.1000/block.two"),
    ):
        state.upsert_catalog_record(
            vault,
            work_id=work_id,
            title=title,
            description="A fixture source.",
            resource=f"https://doi.org/{doi}",
            identifiers={"doi": doi},
            citekey=f"{work_id}2026",
            csl_json={
                "id": f"{work_id}2026",
                "type": "article-journal",
                "title": title,
                "DOI": doi,
                "issued": {"date-parts": [[2026]]},
                "author": [{"family": "River", "given": "Ada"}],
            },
            provider_coverage="full",
            text_status="full-text",
            check_status="checked",
        )

    result = check_source_metadata(
        vault,
        shadow=False,
        machine="integrity-machine",
        commit=True,
    )

    assert [
        (finding["check"], finding["target_id"], finding["reason"], finding["route"])
        for finding in result["findings"]
    ] == [
        (
            "record-linkage",
            "catalog/sources/source-one",
            "possible duplicate source metadata block also matches catalog/sources/source-two "
            "(title/year/first-author)",
            "ask",
        ),
        (
            "record-linkage",
            "catalog/sources/source-two",
            "possible duplicate source metadata block also matches catalog/sources/source-one "
            "(title/year/first-author)",
            "ask",
        ),
    ]
    assert result["attention_path"] == "inbox/work-prompt-record-linkage-source-external-ids.md"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, result["attention_path"]}


def test_source_metadata_check_ignores_unmodeled_entity_external_ids(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    state.replace_external_ids(
        vault,
        [
            {
                "owner_type": "person",
                "owner_id": "https://openalex.org/A1",
                "namespace": "orcid",
                "value": "0000-0002-1825-0097",
            },
            {
                "owner_type": "person",
                "owner_id": "https://openalex.org/A2",
                "namespace": "orcid",
                "value": "https://orcid.org/0000-0002-1825-0097",
            },
        ],
    )

    result = check_source_metadata(
        vault,
        shadow=False,
        machine="integrity-machine",
        commit=True,
    )

    assert result["findings"] == []
    assert result["attention_path"] == ""
    assert result["attention_paths"] == []
    assert result["commit"] == ""


def test_db_capture_does_not_create_entity_identity_findings(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-one",
        "First identity source",
        "A fixture source.",
        "First source text.",
        resource="https://doi.org/10.1000/identity.one",
        identifiers={"doi": "10.1000/identity.one"},
        citekey="identityOne2026",
        provider_coverage="full",
        csl_json={
            "id": "identityOne2026",
            "type": "article-journal",
            "title": "First identity source",
            "DOI": "10.1000/identity.one",
            "issued": {"date-parts": [[2026]]},
            "author": [
                {
                    "family": "River",
                    "given": "Ada",
                    "ORCID": "0000-0001-0000-0001",
                }
            ],
        },
        machine="capture-machine",
    )
    capture_source(
        vault,
        "source-two",
        "Second identity source",
        "A fixture source.",
        "Second source text.",
        resource="https://doi.org/10.1000/identity.two",
        identifiers={"doi": "10.1000/identity.two"},
        citekey="identityTwo2026",
        provider_coverage="full",
        csl_json={
            "id": "identityTwo2026",
            "type": "article-journal",
            "title": "Second identity source",
            "DOI": "10.1000/identity.two",
            "issued": {"date-parts": [[2026]]},
            "author": [
                {
                    "family": "River",
                    "given": "Ada",
                    "ORCID": "0000-0002-0000-0002",
                }
            ],
        },
        machine="capture-machine",
    )

    sync_file_verdicts(vault)
    result = check_source_metadata(vault, shadow=False, machine="integrity-machine")

    assert result["findings"] == []
    assert not (vault / "catalog/sources/source-one/source.md").exists()
    assert not (vault / "catalog/sources/source-two/source.md").exists()
    assert not (vault / "catalog/entities/person-ada-river.md").exists()
