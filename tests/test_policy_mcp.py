"""L1 component test for policy_mcp — extracted from its former --self-test (ADR-44)."""
import policy_mcp as _m
from _util import TestHarness
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_policy_mcp():
    def _run():
        import tempfile

        t = TestHarness()
        check = t.check

        # ---- glob matcher ------------------------------------------------------ #
        check("glob: '**' matches anything",
              path_matches("a/b/c.md", ["**"]))
        check("glob: '*' stays within a segment",
              not path_matches("a/b.md", ["*"]) and path_matches("a.md", ["*"]))
        check("glob: code scope matches nested file",
              path_matches("40-workbench/project-x/06-code/main.py", ["40-workbench/*/06-code/**"]))
        check("glob: code scope rejects sibling folder",
              not path_matches("40-workbench/project-x/04-drafts/d.md", ["40-workbench/*/06-code/**"]))
        check("glob: exact-file pattern matches only that file",
              path_matches("40-workbench/p/01-map/corpus-map.md", ["40-workbench/*/01-map/corpus-map.md"])
              and not path_matches("40-workbench/p/01-map/other.md", ["40-workbench/*/01-map/corpus-map.md"]))
        check("glob: '**/' matches zero middle segments",
              path_matches("a/b.md", ["a/**/b.md"]) and path_matches("a/x/y/b.md", ["a/**/b.md"]))

        # ---- normalize_path: collapse '..' and reject traversal escapes -------- #
        check("normalize_path: collapse interior '..'",
              normalize_path("a/b/../../c") == "c")
        check("normalize_path: collapse multiple '..'",
              normalize_path("40-workbench/x/../../30-synthesis/c.md") == "30-synthesis/c.md")
        check("normalize_path: strip leading './'",
              normalize_path("./a/b.md") == "a/b.md")
        check("normalize_path: strip leading '/'",
              normalize_path("/a/b.md") == "a/b.md")
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
            check("engine denies path-traversal escape",
                  trav_resp["decision"] == "deny" and trav_resp["policy_rule"] == "path.traversal")
            # The traversal attempt must be audited (#214) -- exactly one deny entry,
            # carrying the raw path and the task_id, so intrusion probes leave a trace.
            trav_lines = (trav_vault / AUDIT_RELPATH).read_text(encoding="utf-8").splitlines()
            trav_entry = json.loads(trav_lines[-1]) if trav_lines else {}
            check("engine audits the traversal attempt",
                  len(trav_lines) == 1
                  and trav_entry["decision"] == "deny"
                  and trav_entry["policy_rule"] == "path.traversal"
                  and trav_entry["path"] == "../../etc/passwd"
                  and trav_entry["task_id"] == "T-TRAV")

        # ---- lanes (built directly so the self-test needs no PyYAML) ----------- #
        coder = LanePolicy(
            profile="memoria-coder",
            allow_write=["40-workbench/*/06-code/**"],
            deny_write=["10-inbox/**", "20-sources/**", "30-synthesis/**",
                        "40-workbench/*/04-drafts/**", "50-deliverables/**"],
            require=["audit_log"], write_scope=["40-workbench/*/06-code/"],
        )
        writer = LanePolicy(
            profile="memoria-writer",
            allow_write=["10-inbox/02-answers/**", "40-workbench/*/04-drafts/**",
                         "40-workbench/*/02-framing/**", "30-synthesis/02-reference/**"],
            deny_write=["20-sources/**", "30-synthesis/01-claims/**", "50-deliverables/**"],
            require=["audit_log"],
        )
        socratic = LanePolicy(profile="memoria-socratic", allow_write=[],
                              deny_write=["**"], require=["audit_log"])
        linter = LanePolicy(
            profile="memoria-linter",
            allow_write=["99-system/logs/**"],
            allow_auto_fix_classes=["safe-and-unambiguous", "authorized-targeted"],
            deny_write=["10-inbox/**", "20-sources/**", "30-synthesis/**",
                        "40-workbench/**", "50-deliverables/**"],
            deny_auto_fix_classes=["schema-content", "review-gated-edit"],
            require=["audit_log"], write_scope=["99-system/logs/"],
        )
        # The remaining three lanes mirror their real .memoria/lane-overrides/*.yaml
        # so the gate contract for all seven profiles is unit-covered (closes the
        # hermes-cli protocol's X1 / M4 / V-series write-walls — L2 gate testing).
        librarian = LanePolicy(
            profile="memoria-librarian",
            allow_write=["10-inbox/01-fleeting/**", "10-inbox/03-candidates/**",
                         "20-sources/**"],
            deny_write=["30-synthesis/**", "40-workbench/**", "50-deliverables/**"],
            require=["audit_log"],
            write_scope=["10-inbox/01-fleeting/", "10-inbox/03-candidates/", "20-sources/"],
        )
        mapper = LanePolicy(
            profile="memoria-mapper",
            allow_write=["40-workbench/*/01-map/corpus-map.md",
                         "40-workbench/*/01-map/gap-report.md",
                         "40-workbench/*/01-map/cluster-maps/**"],
            deny_write=["10-inbox/**", "20-sources/**", "30-synthesis/**",
                        "50-deliverables/**"],
            require=["audit_log"], write_scope=["40-workbench/*/01-map/"],
        )
        verifier = LanePolicy(
            profile="memoria-verifier",
            allow_write=["40-workbench/*/05-verification/**", "10-inbox/03-candidates/**"],
            deny_write=["20-sources/**", "30-synthesis/**",
                        "40-workbench/*/04-drafts/**", "50-deliverables/**"],
            require=["audit_log"],
            write_scope=["40-workbench/*/05-verification/", "10-inbox/03-candidates/"],
        )

        d = lambda p, a, pa, fl=None, sk=None: decide(p.profile, a, pa, p, flags=fl, skill_deny_write=sk).decision

        # ---- write decisions --------------------------------------------------- #
        check("Coder write to own code scope -> allow",
              d(coder, "write", "40-workbench/x/06-code/main.py") == "allow")
        check("Coder write to drafts -> deny (lane deny)",
              d(coder, "write", "40-workbench/x/04-drafts/d.md") == "deny")
        check("Coder write to unmapped path -> deny (default-deny)",
              d(coder, "write", "99-nowhere/x.md") == "deny")
        check("Writer write to answers -> allow",
              d(writer, "write", "10-inbox/02-answers/a.md") == "allow")
        check("Writer write to review-gated reference -> dry_run (degrade)",
              d(writer, "write", "30-synthesis/02-reference/r.md") == "dry_run")
        check("Writer write to claims -> deny (lane deny beats degrade)",
              d(writer, "write", "30-synthesis/01-claims/c.md") == "deny")
        check("Socratic write anywhere -> deny (hard write-denial)",
              d(socratic, "write", "10-inbox/01-fleeting/f.md") == "deny")

        # ---- read decisions ---------------------------------------------------- #
        check("Coder read normal zone -> allow",
              d(coder, "read", "20-sources/01-papers/p.md") == "allow")
        check("Coder read review-gated -> allow_with_log",
              d(coder, "read", "30-synthesis/01-claims/c.md") == "allow_with_log")

        # ---- auto_fix class gating (Linter) ------------------------------------ #
        check("Linter auto_fix safe class in logs -> allow_with_log",
              d(linter, "auto_fix", "99-system/logs/audit.jsonl", {"class": "safe-and-unambiguous"}) == "allow_with_log")
        check("Linter auto_fix schema-content -> dry_run",
              d(linter, "auto_fix", "99-system/logs/x.md", {"class": "schema-content"}) == "dry_run")
        check("Linter auto_fix review-gated-edit -> deny",
              d(linter, "auto_fix", "99-system/logs/x.md", {"class": "review-gated-edit"}) == "deny")
        check("Linter auto_fix with no class -> deny",
              d(linter, "auto_fix", "99-system/logs/x.md", None) == "deny")

        # ---- delete / mkdir / report ------------------------------------------- #
        check("Coder delete without authorization -> deny",
              d(coder, "delete", "40-workbench/x/06-code/old.py") == "deny")
        check("Coder delete with explicit_authorization in scope -> allow_with_log",
              d(coder, "delete", "40-workbench/x/06-code/old.py", {"explicit_authorization": True}) == "allow_with_log")
        check("Coder mkdir in write_scope -> allow",
              d(coder, "mkdir", "40-workbench/x/06-code/sub") == "allow")
        check("Coder report -> allow",
              d(coder, "report", "40-workbench/x/06-code/") == "allow")

        # ---- skill-conditional one-way narrowing ------------------------------- #
        # counter-outline narrows Writer to framing-only; drafts then deny.
        co_deny = compose_skill_deny(writer, {"deny": {"write": ["40-workbench/*/04-drafts/**"]}})
        check("counter-outline composes a draft-deny",
              co_deny == ["40-workbench/*/04-drafts/**"])
        check("Writer+counter-outline: draft write now denied",
              d(writer, "write", "40-workbench/x/04-drafts/d.md", None, co_deny) == "deny")
        check("Writer+counter-outline: framing write still allowed",
              d(writer, "write", "40-workbench/x/02-framing/f.md", None, co_deny) == "allow")

        # ---- L2 gate-contract: per-profile write-walls (hermes-cli §4/§5) ------- #
        # Lifted from the protocol's case IDs so the gate contract for librarian /
        # mapper / verifier is unit-tested here, not just observed once at runtime.
        # (A plain allowed write returns "allow" and is *logged* via require:audit_log
        # — the protocol's "allow_with_log row" prose means logged, not the
        # allow_with_log decision, which is for review-gated reads / safe auto-fix.)
        check("L1/L2 Librarian write to candidates + sources -> allow",
              d(librarian, "write", "20-sources/01-papers/smithA.md") == "allow"
              and d(librarian, "write", "10-inbox/03-candidates/c.md") == "allow")
        check("X1 Librarian write to claims -> deny (write-wall)",
              d(librarian, "write", "30-synthesis/01-claims/c.md") == "deny")
        check("Librarian write to deliverables / another lane's map -> deny",
              d(librarian, "write", "50-deliverables/d.md") == "deny"
              and d(librarian, "write", "40-workbench/x/01-map/m.md") == "deny")
        check("M1/M2/M3 Mapper write to its three map artifacts -> allow",
              d(mapper, "write", "40-workbench/x/01-map/corpus-map.md") == "allow"
              and d(mapper, "write", "40-workbench/x/01-map/gap-report.md") == "allow"
              and d(mapper, "write", "40-workbench/x/01-map/cluster-maps/c.md") == "allow")
        check("Mapper write to an unlisted map file -> deny (exact-file scope)",
              d(mapper, "write", "40-workbench/x/01-map/other.md") == "deny")
        check("M4 Mapper write outside its lane -> deny (write-wall)",
              d(mapper, "write", "20-sources/p.md") == "deny"
              and d(mapper, "write", "30-synthesis/01-claims/c.md") == "deny")
        check("V1/V2 Verifier write to verification + gap candidates -> allow",
              d(verifier, "write", "40-workbench/x/05-verification/report.md") == "allow"
              and d(verifier, "write", "10-inbox/03-candidates/gap.md") == "allow")
        check("V1 Verifier write to the draft under test -> deny (no self-edit)",
              d(verifier, "write", "40-workbench/x/04-drafts/draft.md") == "deny")
        check("Verifier write to synthesis -> deny (write-wall)",
              d(verifier, "write", "30-synthesis/01-claims/c.md") == "deny")

        # ---- invalid action + missing task_id ---------------------------------- #
        check("unknown action -> deny",
              d(coder, "frobnicate", "40-workbench/x/06-code/main.py") == "deny")

        # ---- SHA-256 ----------------------------------------------------------- #
        check("empty/missing file hashes to the empty-string sha256",
              sha256_file(Path("/no/such/file/anywhere")) == EMPTY_SHA256)

        # ---- engine: audit append + full request path -------------------------- #
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            lane_dir = vault / LANE_OVERRIDE_RELDIR
            lane_dir.mkdir(parents=True)
            # Write a minimal coder lane so load_lane is exercised when PyYAML is present.
            (lane_dir / "coder.yaml").write_text(
                "profile: memoria-coder\n"
                "policy:\n  allow:\n    write:\n      - \"40-workbench/*/06-code/**\"\n"
                "  deny:\n    write:\n      - \"30-synthesis/**\"\n  require:\n    - audit_log\n"
                "routing:\n  write_scope:\n    - \"40-workbench/*/06-code/\"\n",
                encoding="utf-8")
            engine = PolicyEngine(vault)
            if yaml is not None:
                resp = engine.check("memoria-coder", "write",
                                    "40-workbench/x/06-code/main.py", "TASK-1", "impl")
                check("engine allow includes before_hash", resp.get("before_hash") == EMPTY_SHA256)
                check("engine logged the allow to audit.jsonl", (vault / AUDIT_RELPATH).is_file())
                deny = engine.check("memoria-coder", "write", "30-synthesis/01-claims/c.md", "TASK-1")
                check("engine deny on lane-denied path", deny["decision"] == "deny")
                lines = (vault / AUDIT_RELPATH).read_text(encoding="utf-8").strip().splitlines()
                check("audit has one line per decision", len(lines) == 2)
                check("audit lines are valid JSON", all(json.loads(ln) for ln in lines))
            else:
                print("  SKIP  engine YAML-load checks (PyYAML not installed)")
            # task_id is mandatory
            no_task = engine.check("memoria-coder", "write", "40-workbench/x/06-code/m.py", "")
            check("missing task_id -> deny", no_task["decision"] == "deny")

        return t.summary(label="all" if yaml is not None else "core")
    assert _run() == 0
