"""L1 component test for the policy MCP and split policy core."""

import policy_mcp as _m
import pytest
from _util import CheckHarness

AUDIT_RELPATH = _m.AUDIT_RELPATH
EMPTY_SHA256 = _m.EMPTY_SHA256
LANE_OVERRIDE_RELDIR = _m.LANE_OVERRIDE_RELDIR
LanePolicy = _m.LanePolicy
Path = _m.Path
PolicyEngine = _m.PolicyEngine
compose_skill_deny = _m.compose_skill_deny
decide = _m.decide
json = _m.json
load_lane = _m.load_lane
normalize_path = _m.normalize_path
path_matches = _m.path_matches
sha256_file = _m.sha256_file
yaml = _m.yaml


def test_policy_mcp():
    def _run():
        import tempfile

        t = CheckHarness()
        check = t.check

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
            trav_resp = eng_trav.check("memoria-coder", "write", "../../etc/passwd", "T-TRAV")
            check(
                "engine denies path-traversal escape",
                trav_resp["decision"] == "deny" and trav_resp["policy_rule"] == "path.traversal",
            )
            # The traversal attempt must be audited (#214) -- exactly one deny entry,
            # carrying the raw path and the task_id, so intrusion probes leave a trace.
            trav_lines = (trav_vault / AUDIT_RELPATH).read_text(encoding="utf-8").splitlines()
            trav_entry = json.loads(trav_lines[-1]) if trav_lines else {}
            check(
                "engine audits the traversal attempt",
                len(trav_lines) == 1
                and trav_entry["decision"] == "deny"
                and trav_entry["policy_rule"] == "path.traversal"
                and trav_entry["path"] == "../../etc/passwd"
                and trav_entry["task_id"] == "T-TRAV",
            )

        # ---- lanes (built directly so the self-test needs no PyYAML) ----------- #
        # Mirror the five real .memoria/lane-overrides/*.yaml (ADR-48) so the gate
        # contract for every shipped agent is unit-covered, plus a synthetic
        # maintenance lane exercising the auto-fix class machinery.
        engineer = LanePolicy(
            profile="memoria-engineer",
            allow_write=["projects/*/code/**"],
            deny_write=["notes/**", "catalog/**", "inbox/**", "system/**"],
            require=["audit_log"],
            write_scope=["projects/*/code/"],
        )
        writer = LanePolicy(
            profile="memoria-writer",
            allow_write=["projects/**", "notes/hubs/**"],
            deny_write=["notes/claims/**", "catalog/**", "inbox/**", "system/**"],
            require=["audit_log"],
        )
        copi = LanePolicy(
            profile="memoria-copi", allow_write=[], deny_write=["**"], require=["audit_log"]
        )
        maintenance = LanePolicy(
            profile="memoria-linter-engine",
            allow_write=["system/logs/**"],
            allow_auto_fix_classes=["safe-and-unambiguous", "authorized-targeted"],
            deny_write=["inbox/**", "catalog/**", "notes/**", "projects/**"],
            deny_auto_fix_classes=["schema-content", "review-gated-edit"],
            require=["audit_log"],
            write_scope=["system/logs/"],
        )
        librarian = LanePolicy(
            profile="memoria-librarian",
            allow_write=["inbox/**", "catalog/**", "notes/fleeting/**", "notes/sources/**"],
            deny_write=[
                "notes/claims/**",
                "notes/hubs/**",
                "notes/indexes/**",
                "projects/**",
                "system/**",
            ],
            require=["audit_log"],
            write_scope=["inbox/", "catalog/", "notes/fleeting/", "notes/sources/"],
        )
        peer_reviewer = LanePolicy(
            profile="memoria-peer-reviewer",
            allow_write=["inbox/**"],
            deny_write=["notes/**", "catalog/**", "projects/**", "system/**"],
            require=["audit_log"],
            write_scope=["inbox/"],
        )

        d = lambda p, a, pa, fl=None, sk=None: (
            decide(p.profile, a, pa, p, flags=fl, skill_deny_write=sk).decision
        )

        # ---- write decisions --------------------------------------------------- #
        # B5c: every mutating allow is audited — a write/append/move that passes
        # the lane returns allow_with_log, never a bare (possibly unlogged) allow.
        check(
            "Engineer write to own code scope -> allow_with_log",
            d(engineer, "write", "projects/x/code/main.py") == "allow_with_log",
        )
        check(
            "Engineer write to notes -> deny (lane deny)",
            d(engineer, "write", "notes/sources/d.md") == "deny",
        )
        check(
            "Engineer write to unmapped path -> deny (default-deny)",
            d(engineer, "write", "99-nowhere/x.md") == "deny",
        )
        check(
            "Writer write to project scratch -> allow_with_log",
            d(writer, "write", "projects/x/draft.md") == "allow_with_log",
        )
        check(
            "Writer write to review-gated reference -> dry_run (degrade)",
            d(writer, "write", "notes/hubs/r.md") == "dry_run",
        )
        check(
            "Writer write to claims -> deny (lane deny beats degrade)",
            d(writer, "write", "notes/claims/c.md") == "deny",
        )
        check(
            "Co-PI write anywhere -> deny (hard write-denial)",
            d(copi, "write", "notes/fleeting/f.md") == "deny",
        )

        # ---- read decisions ---------------------------------------------------- #
        check(
            "Engineer read normal zone -> allow",
            d(engineer, "read", "catalog/papers/p.md") == "allow",
        )
        check(
            "Engineer read review-gated -> allow_with_log",
            d(engineer, "read", "notes/claims/c.md") == "allow_with_log",
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
            "Engineer delete with explicit_authorization in scope -> allow_with_log",
            d(engineer, "delete", "projects/x/code/old.py", {"explicit_authorization": True})
            == "allow_with_log",
        )
        check(
            "Engineer mkdir in write_scope -> allow",
            d(engineer, "mkdir", "projects/x/code/sub") == "allow",
        )
        check("Engineer report -> allow", d(engineer, "report", "projects/x/code/") == "allow")

        # ---- skill-conditional one-way narrowing ------------------------------- #
        # counter-outline narrows Writer to framing-only; drafts then deny.
        co_deny = compose_skill_deny(writer, {"deny": {"write": ["projects/*/drafts/**"]}})
        check("counter-outline composes a draft-deny", co_deny == ["projects/*/drafts/**"])
        check(
            "Writer+counter-outline: draft write now denied",
            d(writer, "write", "projects/x/drafts/d.md", None, co_deny) == "deny",
        )
        check(
            "Writer+counter-outline: framing write still allowed (with log)",
            d(writer, "write", "projects/x/framing/f.md", None, co_deny) == "allow_with_log",
        )

        # ---- L2 gate-contract: per-profile write-walls (hermes-cli §4/§5) ------- #
        # Lifted from the protocol's case IDs so the gate contract for librarian /
        # mapper / verifier is unit-tested here, not just observed once at runtime.
        # (Since B5c, every allowed mutating write IS the allow_with_log decision —
        # the audit chain has no unlogged-allow hole left.)
        check(
            "L1/L2 Librarian write to candidates + sources -> allow_with_log",
            d(librarian, "write", "catalog/papers/smithA.md") == "allow_with_log"
            and d(librarian, "write", "inbox/candidate-x.md") == "allow_with_log",
        )
        check(
            "X1 Librarian write to claims -> deny (write-wall)",
            d(librarian, "write", "notes/claims/c.md") == "deny",
        )
        check(
            "Librarian write to projects/system -> deny",
            d(librarian, "write", "projects/x/d.md") == "deny"
            and d(librarian, "write", "system/templates/claim.md") == "deny",
        )
        check(
            "V1/V2 Peer-reviewer write to inbox cards -> allow_with_log",
            d(peer_reviewer, "write", "inbox/flag-broken-citekey.md") == "allow_with_log"
            and d(peer_reviewer, "write", "inbox/gap-missing-rcts.md") == "allow_with_log",
        )
        check(
            "V1 Peer-reviewer write to the draft under test -> deny (no self-edit)",
            d(peer_reviewer, "write", "projects/x/draft.md") == "deny",
        )
        check(
            "Peer-reviewer write to claims -> deny (write-wall)",
            d(peer_reviewer, "write", "notes/claims/c.md") == "deny",
        )

        # ---- invalid action + missing task_id ---------------------------------- #
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
            lane_dir = vault / LANE_OVERRIDE_RELDIR
            lane_dir.mkdir(parents=True)
            # Write a minimal coder lane so load_lane is exercised when PyYAML is present.
            (lane_dir / "coder.yaml").write_text(
                "profile: memoria-coder\n"
                'policy:\n  allow:\n    write:\n      - "40-workbench/*/06-code/**"\n'
                '  deny:\n    write:\n      - "30-synthesis/**"\n  require:\n    - audit_log\n'
                'routing:\n  write_scope:\n    - "40-workbench/*/06-code/"\n',
                encoding="utf-8",
            )
            engine = PolicyEngine(vault)
            if yaml is not None:
                resp = engine.check(
                    "memoria-coder", "write", "40-workbench/x/06-code/main.py", "TASK-1", "impl"
                )
                check("engine allow includes before_hash", resp.get("before_hash") == EMPTY_SHA256)
                check("engine logged the allow to audit.jsonl", (vault / AUDIT_RELPATH).is_file())
                deny = engine.check(
                    "memoria-coder", "write", "30-synthesis/01-claims/c.md", "TASK-1"
                )
                check("engine deny on lane-denied path", deny["decision"] == "deny")
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
                    "memoria-coder",
                    "write",
                    "40-workbench/x/06-code/main.py",
                    "TASK-1",
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
                    "memoria-coder",
                    "write",
                    "40-workbench/x/06-code/main.py",
                    "TASK-1",
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
            # task_id is mandatory
            no_task = engine.check("memoria-coder", "write", "40-workbench/x/06-code/m.py", "")
            check("missing task_id -> deny", no_task["decision"] == "deny")

        return t.summary(label="all" if yaml is not None else "core")

    assert _run() == 0


# Loaded from the real shipped lane-override YAMLs, not in-test mirrors, so a
# lane edit that opens a hole in the template wall fails this test directly.
SHIPPED_PROFILES = (
    "memoria-copi",
    "memoria-engineer",
    "memoria-librarian",
    "memoria-peer-reviewer",
    "memoria-writer",
)


def test_shipped_lanes_deny_template_mutations():
    """#179: every shipped lane ceiling denies every mutating action under
    system/templates/. Agents are blocked here (deny.write `system/**`, Co-PI
    `**`); accidental *human* overwrites are the golden copy's job
    (tests/test_golden_restore.py)."""
    if _m.yaml is None:
        pytest.skip("PyYAML not installed")
    src = Path(__file__).resolve().parent.parent / "src"
    path = "system/templates/claim.md"
    for profile in SHIPPED_PROFILES:
        lane = load_lane(src, profile)
        for action in ("write", "append", "move"):
            dec = decide(profile, action, path, lane)
            assert dec.decision == "deny", (profile, action, dec)
        # delete: even with explicit authorization, templates sit outside every
        # lane's allow.write, so the scope check denies.
        dec = decide(profile, "delete", path, lane, flags={"explicit_authorization": True})
        assert dec.decision == "deny", (profile, "delete", dec)
        # mkdir under templates: outside every routing.write_scope.
        dec = decide(profile, "mkdir", "system/templates/sub", lane)
        assert dec.decision == "deny", (profile, "mkdir", dec)
        # auto_fix: even the two always-eligible classes are scoped to the
        # lane's allow.write, which never reaches system/templates/.
        for cls in ("safe-and-unambiguous", "authorized-targeted"):
            dec = decide(profile, "auto_fix", path, lane, flags={"class": cls})
            assert dec.decision == "deny", (profile, "auto_fix", cls, dec)


def test_open_block_loudness_card_blocks_review_gated_promotion_until_acknowledged(tmp_path):
    lane_dir = tmp_path / LANE_OVERRIDE_RELDIR
    lane_dir.mkdir(parents=True)
    (lane_dir / "writer.yaml").write_text(
        "profile: memoria-writer\n"
        "policy:\n"
        "  allow:\n"
        '    write: ["notes/hubs/**"]\n'
        '  require: ["audit_log"]\n'
        "routing:\n"
        '  write_scope: ["notes/hubs/"]\n',
        encoding="utf-8",
    )
    (tmp_path / "inbox").mkdir()
    blocker = tmp_path / "inbox/block.md"
    blocker.write_text(
        "---\ntitle: Stop\ntype: alert\nlifecycle: proposed\nloudness: block\n---\n",
        encoding="utf-8",
    )

    engine = PolicyEngine(tmp_path)
    blocked = engine.check("memoria-writer", "write", "notes/hubs/h.md", "T-BLOCK")
    assert blocked["decision"] == "deny"
    assert blocked["policy_rule"] == "loudness.block.active"
    assert blocked["blockers"][0]["path"] == "inbox/block.md"

    blocker.write_text(
        "---\ntitle: Stop\ntype: alert\nlifecycle: current\nloudness: block\nresolved: 2026-06-15\n---\n",
        encoding="utf-8",
    )
    unblocked = engine.check("memoria-writer", "write", "notes/hubs/h.md", "T-OPEN")
    assert unblocked["decision"] == "dry_run"
    assert unblocked["policy_rule"] == "review_gated.dry_run"


def test_split_policy_decision_core_imports_without_mcp_server():
    from memoria.runtime.policy.decision import decide
    from memoria.runtime.policy.model import LanePolicy

    lane = LanePolicy(profile="memoria-test", allow_write=["inbox/**"], require=["audit_log"])
    result = decide("memoria-test", "write", "inbox/card.md", lane)

    assert result.decision == "allow_with_log"
    assert result.policy_rule == "Test.write.inbox"
