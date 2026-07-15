"""L1 component test for the split runtime policy core."""

import json
from pathlib import Path

import pytest

from memoria_vault.runtime.policy import (
    AUDIT_RELPATH,
    EMPTY_SHA256,
    POLICY_CONFIG_RELPATH,
    ActorPolicy,
    PolicyEngine,
    compose_skill_deny,
    decide,
    load_actor_policy,
    normalize_path,
    path_matches,
    sha256_file,
)
from tests.helpers import WORKSPACE_SEED


def test_runtime_policy_core():
    import tempfile

    # ---- glob matcher ------------------------------------------------------ #
    assert path_matches("a/b/c.md", ["**"]), "glob: '**' matches anything"
    assert not path_matches("a/b.md", ["*"]) and path_matches("a.md", ["*"]), (
        "glob: '*' stays within a segment"
    )
    assert path_matches("40-workbench/project-x/06-code/main.py", ["40-workbench/*/06-code/**"]), (
        "glob: code scope matches nested file"
    )
    assert not path_matches(
        "40-workbench/project-x/04-drafts/d.md", ["40-workbench/*/06-code/**"]
    ), "glob: code scope rejects sibling folder"
    assert path_matches(
        "40-workbench/p/01-map/corpus-map.md", ["40-workbench/*/01-map/corpus-map.md"]
    ) and not path_matches(
        "40-workbench/p/01-map/other.md", ["40-workbench/*/01-map/corpus-map.md"]
    ), "glob: exact-file pattern matches only that file"
    assert path_matches("a/b.md", ["a/**/b.md"]) and path_matches("a/x/y/b.md", ["a/**/b.md"]), (
        "glob: '**/' matches zero middle segments"
    )

    # ---- normalize_path: collapse '..' and reject traversal escapes -------- #
    assert normalize_path("a/b/../../c") == "c", "normalize_path: collapse interior '..'"
    assert normalize_path("40-workbench/x/../../30-synthesis/c.md") == "30-synthesis/c.md", (
        "normalize_path: collapse multiple '..'"
    )
    assert normalize_path("./a/b.md") == "a/b.md", "normalize_path: strip leading './'"
    assert normalize_path("/a/b.md") == "a/b.md", "normalize_path: strip leading '/'"
    with pytest.raises(ValueError):
        normalize_path("../../etc/passwd")
    with pytest.raises(ValueError):
        normalize_path("a/../../../etc/passwd")

    # ---- engine: traversal attempt -> deny --------------------------------- #
    with tempfile.TemporaryDirectory() as td_trav:
        trav_vault = Path(td_trav)
        eng_trav = PolicyEngine(trav_vault)
        trav_resp = eng_trav.check("operation", "write", "../../etc/passwd", "REQ-TRAV")
        assert trav_resp["decision"] == "deny" and trav_resp["policy_rule"] == "path.traversal", (
            "engine denies path-traversal escape"
        )
        # The traversal attempt must be audited -- exactly one deny entry,
        # carrying the raw path and the request_id, so intrusion probes leave a trace.
        trav_lines = (trav_vault / AUDIT_RELPATH).read_text(encoding="utf-8").splitlines()
        trav_entry = json.loads(trav_lines[-1]) if trav_lines else {}
        assert (
            len(trav_lines) == 1
            and trav_entry["decision"] == "deny"
            and trav_entry["policy_rule"] == "path.traversal"
            and trav_entry["path"] == "../../etc/passwd"
            and trav_entry["request_id"] == "REQ-TRAV"
        ), "engine audits the traversal attempt"

    # ---- actor policies (built directly so the self-test needs no PyYAML) -- #
    engineer = ActorPolicy(
        actor="engineer",
        allow_write=[],
        deny_write=[
            "digests/**",
            "fulltexts/**",
            "notes/**",
            "hubs/**",
            "projects/**",
            "knowledge/**",
            "catalog/**",
            "inbox/**",
            "system/**",
        ],
        require=["audit_log"],
        write_scope=[],
    )
    writer = ActorPolicy(
        actor="writer",
        allow_write=[],
        deny_write=[
            "digests/**",
            "fulltexts/**",
            "notes/**",
            "hubs/**",
            "projects/**",
            "knowledge/**",
            "catalog/**",
            "inbox/**",
            "system/**",
        ],
        require=["audit_log"],
        write_scope=[],
    )
    copi = ActorPolicy(actor="copi", allow_write=[], deny_write=["**"], require=["audit_log"])
    write_fixture = ActorPolicy(
        actor="write-fixture",
        allow_write=["projects/**"],
        deny_write=[
            "digests/**",
            "fulltexts/**",
            "notes/**",
            "hubs/**",
            "catalog/**",
            "inbox/**",
            "system/**",
        ],
        require=["audit_log"],
        write_scope=["projects/"],
    )
    maintenance = ActorPolicy(
        actor="integrity",
        allow_write=["system/logs/**"],
        allow_auto_fix_classes=["safe-and-unambiguous", "authorized-targeted"],
        deny_write=[
            "inbox/**",
            "catalog/**",
            "digests/**",
            "fulltexts/**",
            "notes/**",
            "hubs/**",
            "projects/**",
        ],
        deny_auto_fix_classes=["schema-content", "review-gated-edit"],
        require=["audit_log"],
        write_scope=["system/logs/"],
    )
    cataloger = ActorPolicy(
        actor="cataloger",
        allow_write=[],
        deny_write=[
            "digests/**",
            "fulltexts/**",
            "notes/**",
            "hubs/**",
            "projects/**",
            "knowledge/**",
            "catalog/**",
            "capabilities/**",
            "inbox/**",
            "system/**",
        ],
        require=["audit_log"],
        write_scope=[
            ".memoria/staging/fulltexts/",
            ".memoria/staging/digests/",
            ".memoria/staging/notes/",
        ],
    )
    reviewer = ActorPolicy(
        actor="reviewer",
        allow_write=[],
        deny_write=[
            "digests/**",
            "fulltexts/**",
            "notes/**",
            "hubs/**",
            "projects/**",
            "knowledge/**",
            "catalog/**",
            "capabilities/**",
            "inbox/**",
            "system/**",
        ],
        require=["audit_log"],
        write_scope=[],
    )

    d = lambda p, a, pa, fl=None, sk=None: (
        decide(p.actor, a, pa, p, flags=fl, skill_deny_write=sk).decision
    )

    # ---- write decisions --------------------------------------------------- #
    # Every mutating allow is audited -- a write/append/move that passes
    # the policy returns allow_with_log, never a bare unlogged allow.
    assert d(write_fixture, "write", "projects/x/code/main.py") == "allow_with_log", (
        "Write fixture write to own scope -> allow_with_log"
    )
    assert d(engineer, "write", "catalog/sources/d/source.md") == "deny", (
        "Engineer write to notes -> deny (policy deny)"
    )
    assert d(engineer, "write", "99-nowhere/x.md") == "deny", (
        "Engineer write to unmapped path -> deny (default-deny)"
    )
    assert d(writer, "write", "projects/x/draft.md") == "deny", (
        "Writer write to project scratch -> deny (deferred)"
    )
    assert d(writer, "write", "hubs/r.md") == "deny", (
        "Writer write to review-gated reference -> deny (deferred)"
    )
    assert d(writer, "write", "notes/c.md") == "deny", (
        "Writer write to claims -> deny (policy deny beats degrade)"
    )
    assert d(copi, "write", "notes/f.md") == "deny", (
        "Co-PI write anywhere -> deny (hard write-denial)"
    )

    # ---- read decisions ---------------------------------------------------- #
    assert d(engineer, "read", "catalog/sources/p/source.md") == "allow", (
        "Engineer read normal zone -> allow"
    )
    assert d(engineer, "read", "notes/c.md") == "allow_with_log", (
        "Engineer read review-gated -> allow_with_log"
    )

    # ---- auto_fix class gating (Linter) ------------------------------------ #
    assert (
        d(maintenance, "auto_fix", "system/logs/audit.jsonl", {"class": "safe-and-unambiguous"})
        == "allow_with_log"
    ), "Maintenance auto_fix safe class in logs -> allow_with_log"
    assert (
        d(maintenance, "auto_fix", "system/logs/x.md", {"class": "schema-content"}) == "dry_run"
    ), "Maintenance auto_fix schema-content -> dry_run"
    assert (
        d(maintenance, "auto_fix", "system/logs/x.md", {"class": "review-gated-edit"}) == "deny"
    ), "Maintenance auto_fix review-gated-edit -> deny"
    assert d(maintenance, "auto_fix", "system/logs/x.md", None) == "deny", (
        "Maintenance auto_fix with no class -> deny"
    )

    # ---- delete / mkdir / report ------------------------------------------- #
    assert d(engineer, "delete", "projects/x/code/old.py") == "deny", (
        "Engineer delete without authorization -> deny"
    )
    assert (
        d(write_fixture, "delete", "projects/x/code/old.py", {"explicit_authorization": True})
        == "allow_with_log"
    ), "Write fixture delete with explicit_authorization in scope -> allow_with_log"
    assert d(write_fixture, "mkdir", "projects/x/code/sub") == "allow", (
        "Write fixture mkdir in write_scope -> allow"
    )
    assert d(engineer, "report", "projects/x/code/") == "allow", "Engineer report -> allow"

    # ---- skill-conditional one-way narrowing ------------------------------- #
    # counter-outline narrows a write-enabled fixture to framing-only; drafts then deny.
    co_deny = compose_skill_deny({"deny": {"write": ["projects/*/drafts/**"]}})
    assert co_deny == ["projects/*/drafts/**"], "counter-outline composes a draft-deny"
    assert d(write_fixture, "write", "projects/x/drafts/d.md", None, co_deny) == "deny", (
        "Writer+counter-outline: draft write now denied"
    )
    assert (
        d(write_fixture, "write", "projects/x/framing/f.md", None, co_deny) == "allow_with_log"
    ), "Writer+counter-outline: framing write still allowed (with log)"

    # ---- L2 gate-contract: adapter write walls ----------------------------- #
    # Lifted from the protocol's case IDs so the gate contract for librarian /
    # mapper / verifier is unit-tested here, not just observed once at runtime.
    # (Since B5c, every allowed mutating write IS the allow_with_log decision —
    # the audit chain has no unlogged-allow hole left.)
    assert (
        d(cataloger, "write", "catalog/sources/smith/source.md") == "deny"
        and d(cataloger, "write", "inbox/candidate-x.md") == "deny"
    ), "Librarian direct write to catalog/inbox -> deny"
    assert d(cataloger, "write", "notes/c.md") == "deny", (
        "X1 Librarian write to claims -> deny (write-wall)"
    )
    assert (
        d(cataloger, "write", "projects/x/d.md") == "deny"
        and d(cataloger, "write", ".memoria/templates/claim.md") == "deny"
    ), "Librarian write to projects/system -> deny"
    assert (
        d(reviewer, "write", "inbox/flag-broken-citekey.md") == "deny"
        and d(reviewer, "write", "inbox/gap-missing-rcts.md") == "deny"
    ), "Peer-reviewer direct write to inbox cards -> deny"
    assert d(reviewer, "write", "projects/x/draft.md") == "deny", (
        "V1 Peer-reviewer write to the draft under test -> deny (no self-edit)"
    )
    assert d(reviewer, "write", "notes/c.md") == "deny", (
        "Peer-reviewer write to claims -> deny (write-wall)"
    )

    # ---- invalid action + missing request_id ------------------------------- #
    assert d(engineer, "frobnicate", "projects/x/code/main.py") == "deny", "unknown action -> deny"

    # ---- SHA-256 ----------------------------------------------------------- #
    assert sha256_file(Path("/no/such/file/anywhere")) == EMPTY_SHA256, (
        "empty/missing file hashes to the empty-string sha256"
    )

    # ---- engine: audit append + full request path -------------------------- #
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        config = vault / POLICY_CONFIG_RELPATH
        config.parent.mkdir(parents=True)
        # Write a minimal actor policy so load_actor_policy is exercised.
        config.write_text(
            "version: 1\n"
            "actors:\n"
            "  operation:\n"
            "    allow:\n"
            '      write: ["40-workbench/*/06-code/**"]\n'
            "    deny:\n"
            '      write: ["30-synthesis/**"]\n'
            '    require: ["audit_log"]\n'
            '    write_scope: ["40-workbench/*/06-code/"]\n',
            encoding="utf-8",
        )
        engine = PolicyEngine(vault)
        resp = engine.check("operation", "write", "40-workbench/x/06-code/main.py", "REQ-1", "impl")
        assert resp.get("before_hash") == EMPTY_SHA256, "engine allow includes before_hash"
        assert (vault / AUDIT_RELPATH).is_file(), "engine logged the allow to audit.jsonl"
        deny = engine.check("operation", "write", "30-synthesis/01-claims/c.md", "REQ-1")
        assert deny["decision"] == "deny", "engine deny on policy-denied path"
        lines = (vault / AUDIT_RELPATH).read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2, "audit has one line per decision"
        assert all(json.loads(ln) for ln in lines), "audit lines are valid JSON"
        first = json.loads(lines[0])
        assert first["schema_version"] == 2 and first["review_mode"] == "blocking", (
            "audit stamps review-mode study arm"
        )
        # B5d: complete_write validates the caller's before_hash against the
        # pre-decision audit record — a different hash is logged, not trusted.
        done = engine.complete_write(
            "operation",
            "write",
            "40-workbench/x/06-code/main.py",
            "REQ-1",
            "sha256:" + "f" * 64,
        )
        last = json.loads(
            (vault / AUDIT_RELPATH).read_text(encoding="utf-8").strip().splitlines()[-1]
        )
        assert (
            done["ok"]
            and last["decision"] == "write_complete"
            and last.get("hash_mismatch") is True
            and last.get("expected_before_hash") == EMPTY_SHA256
        ), "complete_write flags a before_hash mismatch"
        done2 = engine.complete_write(
            "operation",
            "write",
            "40-workbench/x/06-code/main.py",
            "REQ-1",
            EMPTY_SHA256,
        )
        last2 = json.loads(
            (vault / AUDIT_RELPATH).read_text(encoding="utf-8").strip().splitlines()[-1]
        )
        assert done2["ok"] and "hash_mismatch" not in last2, (
            "complete_write with the matching before_hash is clean"
        )
        # request_id is mandatory
        no_request = engine.check("operation", "write", "40-workbench/x/06-code/m.py", "")
        assert no_request["decision"] == "deny", "missing request_id -> deny"


def test_package_seed_no_longer_ships_adapter_policy_config():
    """The standalone package seed ships no adapter policy config."""
    src = WORKSPACE_SEED
    assert not (src / POLICY_CONFIG_RELPATH).exists()
    with pytest.raises(FileNotFoundError):
        load_actor_policy(src, "adapter")


def test_open_block_loudness_card_blocks_review_gated_promotion_until_acknowledged(tmp_path):
    config = tmp_path / POLICY_CONFIG_RELPATH
    config.parent.mkdir(parents=True)
    config.write_text(
        "version: 1\n"
        "actors:\n"
        "  operation:\n"
        "    allow:\n"
        '      write: ["hubs/**"]\n'
        '    require: ["audit_log"]\n'
        '    write_scope: ["hubs/"]\n',
        encoding="utf-8",
    )
    (tmp_path / "inbox").mkdir()
    blocker = tmp_path / "inbox/block.md"
    blocker.write_text(
        "---\n"
        "title: Stop\n"
        "projection: attention\n"
        "attention_kind: alert\n"
        "attention_status: open\n"
        "loudness: block\n"
        "---\n",
        encoding="utf-8",
    )

    engine = PolicyEngine(tmp_path)
    blocked = engine.check("operation", "write", "hubs/h.md", "REQ-BLOCK")
    assert blocked["decision"] == "deny"
    assert blocked["policy_rule"] == "loudness.block.active"
    assert blocked["blockers"][0]["path"] == "inbox/block.md"

    blocker.write_text(
        "---\n"
        "title: Stop\n"
        "projection: attention\n"
        "attention_kind: alert\n"
        "attention_status: resolved\n"
        "loudness: block\n"
        "resolved_at: 2026-06-15\n"
        "---\n",
        encoding="utf-8",
    )
    unblocked = engine.check("operation", "write", "hubs/h.md", "REQ-OPEN")
    assert unblocked["decision"] == "dry_run"
    assert unblocked["policy_rule"] == "review_gated.dry_run"


def test_split_policy_decision_core_imports_without_mcp_server():
    from memoria_vault.runtime.policy.decision import decide
    from memoria_vault.runtime.policy.model import ActorPolicy

    policy = ActorPolicy(actor="adapter", allow_write=["inbox/**"], require=["audit_log"])
    result = decide("adapter", "write", "inbox/attention.md", policy)

    assert result.decision == "allow_with_log"
    assert result.policy_rule == "Adapter.write.inbox"
