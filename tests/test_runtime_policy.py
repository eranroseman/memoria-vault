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
from memoria_vault.runtime.policy.workspace import yaml


def test_runtime_policy_core():
    def _run():
        import tempfile

        def check(name: str, cond: bool) -> None:
            assert cond, name

        # ---- glob matcher ------------------------------------------------------ #
        check("glob: '**' matches anything", path_matches("a/b/c.md", ["**"]))
        check(
            "glob: '*' stays within a segment",
            not path_matches("a/b.md", ["*"]) and path_matches("a.md", ["*"]),
        )
        check(
            "glob: code scope matches nested file",
            path_matches("40-workbench/project-x/06-code/main.py", ["40-workbench/*/06-code/**"]),
        )
        check(
            "glob: code scope rejects sibling folder",
            not path_matches(
                "40-workbench/project-x/04-drafts/d.md", ["40-workbench/*/06-code/**"]
            ),
        )
        check(
            "glob: exact-file pattern matches only that file",
            path_matches(
                "40-workbench/p/01-map/corpus-map.md", ["40-workbench/*/01-map/corpus-map.md"]
            )
            and not path_matches(
                "40-workbench/p/01-map/other.md", ["40-workbench/*/01-map/corpus-map.md"]
            ),
        )
        check(
            "glob: '**/' matches zero middle segments",
            path_matches("a/b.md", ["a/**/b.md"]) and path_matches("a/x/y/b.md", ["a/**/b.md"]),
        )

        # ---- normalize_path: collapse '..' and reject traversal escapes -------- #
        check("normalize_path: collapse interior '..'", normalize_path("a/b/../../c") == "c")
        check(
            "normalize_path: collapse multiple '..'",
            normalize_path("40-workbench/x/../../30-synthesis/c.md") == "30-synthesis/c.md",
        )
        check("normalize_path: strip leading './'", normalize_path("./a/b.md") == "a/b.md")
        check("normalize_path: strip leading '/'", normalize_path("/a/b.md") == "a/b.md")
        try:
            normalize_path("../../etc/passwd")
            check("normalize_path: reject escape above root", False)
        except ValueError:
            check("normalize_path: reject escape above root", True)
        try:
            normalize_path("a/../../../etc/passwd")
            check("normalize_path: reject deep escape above root", False)
        except ValueError:
            check("normalize_path: reject deep escape above root", True)

        # ---- engine: traversal attempt -> deny --------------------------------- #
        with tempfile.TemporaryDirectory() as td_trav:
            trav_vault = Path(td_trav)
            eng_trav = PolicyEngine(trav_vault)
            trav_resp = eng_trav.check("operation", "write", "../../etc/passwd", "REQ-TRAV")
            check(
                "engine denies path-traversal escape",
                trav_resp["decision"] == "deny" and trav_resp["policy_rule"] == "path.traversal",
            )
            # The traversal attempt must be audited -- exactly one deny entry,
            # carrying the raw path and the request_id, so intrusion probes leave a trace.
            trav_lines = (trav_vault / AUDIT_RELPATH).read_text(encoding="utf-8").splitlines()
            trav_entry = json.loads(trav_lines[-1]) if trav_lines else {}
            check(
                "engine audits the traversal attempt",
                len(trav_lines) == 1
                and trav_entry["decision"] == "deny"
                and trav_entry["policy_rule"] == "path.traversal"
                and trav_entry["path"] == "../../etc/passwd"
                and trav_entry["request_id"] == "REQ-TRAV",
            )

        # ---- actor policies (built directly so the self-test needs no PyYAML) -- #
        engineer = ActorPolicy(
            actor="engineer",
            allow_write=[],
            deny_write=["notes/**", "knowledge/**", "catalog/**", "inbox/**", "system/**"],
            require=["audit_log"],
            write_scope=[],
        )
        writer = ActorPolicy(
            actor="writer",
            allow_write=[],
            deny_write=["notes/**", "knowledge/**", "catalog/**", "inbox/**", "system/**"],
            require=["audit_log"],
            write_scope=[],
        )
        copi = ActorPolicy(actor="copi", allow_write=[], deny_write=["**"], require=["audit_log"])
        write_fixture = ActorPolicy(
            actor="write-fixture",
            allow_write=["projects/**"],
            deny_write=["knowledge/notes/**", "catalog/**", "inbox/**", "system/**"],
            require=["audit_log"],
            write_scope=["projects/"],
        )
        maintenance = ActorPolicy(
            actor="integrity",
            allow_write=["system/logs/**"],
            allow_auto_fix_classes=["safe-and-unambiguous", "authorized-targeted"],
            deny_write=["inbox/**", "catalog/**", "notes/**", "projects/**"],
            deny_auto_fix_classes=["schema-content", "review-gated-edit"],
            require=["audit_log"],
            write_scope=["system/logs/"],
        )
        cataloger = ActorPolicy(
            actor="cataloger",
            allow_write=[],
            deny_write=[
                "catalog/**",
                "knowledge/**",
                "capabilities/**",
                "inbox/**",
                "notes/**",
                "projects/**",
                "system/**",
            ],
            require=["audit_log"],
            write_scope=[".memoria/staging/catalog/", ".memoria/staging/knowledge/"],
        )
        reviewer = ActorPolicy(
            actor="reviewer",
            allow_write=[],
            deny_write=[
                "notes/**",
                "knowledge/**",
                "catalog/**",
                "capabilities/**",
                "inbox/**",
                "projects/**",
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
        check(
            "Write fixture write to own scope -> allow_with_log",
            d(write_fixture, "write", "projects/x/code/main.py") == "allow_with_log",
        )
        check(
            "Engineer write to notes -> deny (policy deny)",
            d(engineer, "write", "catalog/sources/d/source.md") == "deny",
        )
        check(
            "Engineer write to unmapped path -> deny (default-deny)",
            d(engineer, "write", "99-nowhere/x.md") == "deny",
        )
        check(
            "Writer write to project scratch -> deny (deferred)",
            d(writer, "write", "projects/x/draft.md") == "deny",
        )
        check(
            "Writer write to review-gated reference -> deny (deferred)",
            d(writer, "write", "knowledge/hubs/r.md") == "deny",
        )
        check(
            "Writer write to claims -> deny (policy deny beats degrade)",
            d(writer, "write", "knowledge/notes/c.md") == "deny",
        )
        check(
            "Co-PI write anywhere -> deny (hard write-denial)",
            d(copi, "write", "knowledge/notes/f.md") == "deny",
        )

        # ---- read decisions ---------------------------------------------------- #
        check(
            "Engineer read normal zone -> allow",
            d(engineer, "read", "catalog/sources/p/source.md") == "allow",
        )
        check(
            "Engineer read review-gated -> allow_with_log",
            d(engineer, "read", "knowledge/notes/c.md") == "allow_with_log",
        )

        # ---- auto_fix class gating (Linter) ------------------------------------ #
        check(
            "Maintenance auto_fix safe class in logs -> allow_with_log",
            d(maintenance, "auto_fix", "system/logs/audit.jsonl", {"class": "safe-and-unambiguous"})
            == "allow_with_log",
        )
        check(
            "Maintenance auto_fix schema-content -> dry_run",
            d(maintenance, "auto_fix", "system/logs/x.md", {"class": "schema-content"})
            == "dry_run",
        )
        check(
            "Maintenance auto_fix review-gated-edit -> deny",
            d(maintenance, "auto_fix", "system/logs/x.md", {"class": "review-gated-edit"})
            == "deny",
        )
        check(
            "Maintenance auto_fix with no class -> deny",
            d(maintenance, "auto_fix", "system/logs/x.md", None) == "deny",
        )

        # ---- delete / mkdir / report ------------------------------------------- #
        check(
            "Engineer delete without authorization -> deny",
            d(engineer, "delete", "projects/x/code/old.py") == "deny",
        )
        check(
            "Write fixture delete with explicit_authorization in scope -> allow_with_log",
            d(write_fixture, "delete", "projects/x/code/old.py", {"explicit_authorization": True})
            == "allow_with_log",
        )
        check(
            "Write fixture mkdir in write_scope -> allow",
            d(write_fixture, "mkdir", "projects/x/code/sub") == "allow",
        )
        check("Engineer report -> allow", d(engineer, "report", "projects/x/code/") == "allow")

        # ---- skill-conditional one-way narrowing ------------------------------- #
        # counter-outline narrows a write-enabled fixture to framing-only; drafts then deny.
        co_deny = compose_skill_deny(write_fixture, {"deny": {"write": ["projects/*/drafts/**"]}})
        check("counter-outline composes a draft-deny", co_deny == ["projects/*/drafts/**"])
        check(
            "Writer+counter-outline: draft write now denied",
            d(write_fixture, "write", "projects/x/drafts/d.md", None, co_deny) == "deny",
        )
        check(
            "Writer+counter-outline: framing write still allowed (with log)",
            d(write_fixture, "write", "projects/x/framing/f.md", None, co_deny) == "allow_with_log",
        )

        # ---- L2 gate-contract: adapter write walls ----------------------------- #
        # Lifted from the protocol's case IDs so the gate contract for librarian /
        # mapper / verifier is unit-tested here, not just observed once at runtime.
        # (Since B5c, every allowed mutating write IS the allow_with_log decision —
        # the audit chain has no unlogged-allow hole left.)
        check(
            "Librarian direct write to catalog/inbox -> deny",
            d(cataloger, "write", "catalog/sources/smith/source.md") == "deny"
            and d(cataloger, "write", "inbox/candidate-x.md") == "deny",
        )
        check(
            "X1 Librarian write to claims -> deny (write-wall)",
            d(cataloger, "write", "knowledge/notes/c.md") == "deny",
        )
        check(
            "Librarian write to projects/system -> deny",
            d(cataloger, "write", "projects/x/d.md") == "deny"
            and d(cataloger, "write", "system/templates/claim.md") == "deny",
        )
        check(
            "Peer-reviewer direct write to inbox cards -> deny",
            d(reviewer, "write", "inbox/flag-broken-citekey.md") == "deny"
            and d(reviewer, "write", "inbox/gap-missing-rcts.md") == "deny",
        )
        check(
            "V1 Peer-reviewer write to the draft under test -> deny (no self-edit)",
            d(reviewer, "write", "projects/x/draft.md") == "deny",
        )
        check(
            "Peer-reviewer write to claims -> deny (write-wall)",
            d(reviewer, "write", "knowledge/notes/c.md") == "deny",
        )

        # ---- invalid action + missing request_id ------------------------------- #
        check(
            "unknown action -> deny", d(engineer, "frobnicate", "projects/x/code/main.py") == "deny"
        )

        # ---- SHA-256 ----------------------------------------------------------- #
        check(
            "empty/missing file hashes to the empty-string sha256",
            sha256_file(Path("/no/such/file/anywhere")) == EMPTY_SHA256,
        )

        # ---- engine: audit append + full request path -------------------------- #
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            config = vault / POLICY_CONFIG_RELPATH
            config.parent.mkdir(parents=True)
            # Write a minimal actor policy so load_actor_policy is exercised when PyYAML is present.
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
            if yaml is not None:
                resp = engine.check(
                    "operation", "write", "40-workbench/x/06-code/main.py", "REQ-1", "impl"
                )
                check("engine allow includes before_hash", resp.get("before_hash") == EMPTY_SHA256)
                check("engine logged the allow to audit.jsonl", (vault / AUDIT_RELPATH).is_file())
                deny = engine.check("operation", "write", "30-synthesis/01-claims/c.md", "REQ-1")
                check("engine deny on policy-denied path", deny["decision"] == "deny")
                lines = (vault / AUDIT_RELPATH).read_text(encoding="utf-8").strip().splitlines()
                check("audit has one line per decision", len(lines) == 2)
                check("audit lines are valid JSON", all(json.loads(ln) for ln in lines))
                first = json.loads(lines[0])
                check(
                    "audit stamps review-mode study arm",
                    first["schema_version"] == 2 and first["review_mode"] == "blocking",
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
                check(
                    "complete_write flags a before_hash mismatch",
                    done["ok"]
                    and last["decision"] == "write_complete"
                    and last.get("hash_mismatch") is True
                    and last.get("expected_before_hash") == EMPTY_SHA256,
                )
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
                check(
                    "complete_write with the matching before_hash is clean",
                    done2["ok"] and "hash_mismatch" not in last2,
                )
            else:
                print("  SKIP  engine YAML-load checks (PyYAML not installed)")
            # request_id is mandatory
            no_request = engine.check("operation", "write", "40-workbench/x/06-code/m.py", "")
            check("missing request_id -> deny", no_request["decision"] == "deny")

    _run()


def test_template_no_longer_ships_adapter_policy_config():
    """The standalone template ships no adapter policy config."""
    if yaml is None:
        pytest.skip("PyYAML not installed")
    src = Path(__file__).resolve().parent.parent / "vault-template"
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
        '      write: ["knowledge/hubs/**"]\n'
        '    require: ["audit_log"]\n'
        '    write_scope: ["knowledge/hubs/"]\n',
        encoding="utf-8",
    )
    (tmp_path / "inbox").mkdir()
    blocker = tmp_path / "inbox/block.md"
    blocker.write_text(
        "---\ntitle: Stop\ntype: alert\nlifecycle: proposed\nloudness: block\n---\n",
        encoding="utf-8",
    )

    engine = PolicyEngine(tmp_path)
    blocked = engine.check("operation", "write", "knowledge/hubs/h.md", "REQ-BLOCK")
    assert blocked["decision"] == "deny"
    assert blocked["policy_rule"] == "loudness.block.active"
    assert blocked["blockers"][0]["path"] == "inbox/block.md"

    blocker.write_text(
        "---\ntitle: Stop\ntype: alert\nlifecycle: current\nloudness: block\nresolved: 2026-06-15\n---\n",
        encoding="utf-8",
    )
    unblocked = engine.check("operation", "write", "knowledge/hubs/h.md", "REQ-OPEN")
    assert unblocked["decision"] == "dry_run"
    assert unblocked["policy_rule"] == "review_gated.dry_run"


def test_split_policy_decision_core_imports_without_mcp_server():
    from memoria_vault.runtime.policy.decision import decide
    from memoria_vault.runtime.policy.model import ActorPolicy

    policy = ActorPolicy(actor="adapter", allow_write=["inbox/**"], require=["audit_log"])
    result = decide("adapter", "write", "inbox/attention.md", policy)

    assert result.decision == "allow_with_log"
    assert result.policy_rule == "Adapter.write.inbox"
