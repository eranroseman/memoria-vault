"""L1 component test for policy_hook — extracted from its former --self-test (ADR-44)."""
import policy_hook as _m
from _util import TestHarness
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_policy_hook():
    def _run():
        __file__ = _m.__file__
        import tempfile

        t = TestHarness()
        check = t.check

        # classify / extract_path -------------------------------------------------
        check("classify: patch -> write", classify("obsidian_patch_content") == "write")
        check("classify: append -> append", classify("obsidian_append_content") == "append")
        check("classify: delete -> delete", classify("obsidian_delete_file") == "delete")
        check("classify: prefixed write matched", classify("mcp__obsidian__put_content") == "write")
        check("classify: read tool -> None", classify("obsidian_get_file_contents") is None)
        check("classify: search -> None", classify("obsidian_simple_search") is None)
        check("classify: terminal -> None (shell ungated)", classify("terminal") is None)
        check("classify: process -> None", classify("process") is None)
        # Hermes `file` toolset writes (Coder/Linter) -- gated; reads are not.
        check("classify: write_file -> write", classify("write_file") == "write")
        check("classify: bare patch -> write", classify("patch") == "write")
        check("classify: prefixed file write", classify("file__write_file") == "write")
        check("classify: read_file -> None", classify("read_file") is None)
        check("classify: search_files -> None", classify("search_files") is None)
        check("extract_path: filepath", extract_path({"filepath": "notes/source/x.md"}) == "notes/source/x.md")
        check("extract_path: file_path", extract_path({"file_path": "notes/source/y.md"}) == "notes/source/y.md")

        # evaluate against a temp vault + real lane files -------------------------
        with tempfile.TemporaryDirectory() as td:
            # Build <vault>/.memoria/{lane-overrides,mcp}/ and copy policy_mcp.py in so
            # the hook's import + parents[2] vault resolution both work.
            vault = Path(td)
            lanes = vault / ".memoria" / "lane-overrides"
            lanes.mkdir(parents=True)
            (vault / ".memoria" / "mcp").mkdir(parents=True)
            import shutil
            mcp_src = Path(__file__).resolve().parent
            shutil.copy(mcp_src / "policy_mcp.py",
                        vault / ".memoria" / "mcp" / "policy_mcp.py")
            shutil.copy(mcp_src / "_shared.py",
                        vault / ".memoria" / "mcp" / "_shared.py")
            (lanes / "writer.yaml").write_text(
                "profile: memoria-writer\npolicy:\n  allow:\n    write:\n"
                "      - \"inbox/**\"\n      - \"notes/hubs/**\"\n"
                "  deny:\n    write:\n      - \"notes/claims/**\"\n"
                "  require:\n    - audit_log\nrouting:\n  write_scope:\n    - \"inbox/\"\n",
                encoding="utf-8")

            ev = lambda tool, path: evaluate_pre(
                {"tool_name": tool, "tool_input": {"filepath": path},
                 "extra": {"task_id": "T1"}}, "memoria-writer", vault)

            check("read tool not gated -> {}", ev("obsidian_get_file_contents", "x.md") == {})
            check("allowed write -> {}", ev("obsidian_patch_content", "inbox/a.md") == {})
            r_dry = ev("obsidian_patch_content", "notes/hubs/r.md")
            check("review-gated write -> block", r_dry.get("decision") == "block" and "review-gated" in r_dry["reason"])
            r_deny = ev("obsidian_delete_file", "notes/claims/c.md")
            check("denied write -> block", r_deny.get("decision") == "block")
            # missing task_id -> fail-closed block
            r_fc = evaluate_pre({"tool_name": "obsidian_patch_content",
                                 "tool_input": {"filepath": "inbox/a.md"}},
                                "memoria-writer", vault)
            check("missing task_id -> fail-closed block", r_fc.get("decision") == "block")

            # native obsidian MCP (Local REST API plugin) tool names are gated the same -
            check("native vault_write allowed zone -> {}",
                  ev("mcp_obsidian_vault_write", "inbox/n.md") == {})
            check("native vault_write denied zone -> block",
                  ev("mcp_obsidian_vault_write", "notes/claims/c.md").get("decision") == "block")
            # hard-deny: blocked even in an ALLOWED zone (overrides the lane check)
            check("native command_execute -> hard block",
                  ev("mcp_obsidian_command_execute", "").get("decision") == "block")
            check("native vault_delete (allowed zone) -> hard block",
                  ev("mcp_obsidian_vault_delete", "inbox/a.md").get("decision") == "block")
            check("native vault_move (allowed zone) -> hard block",
                  ev("mcp_obsidian_vault_move", "inbox/a.md").get("decision") == "block")

            # Hermes `file` toolset writes are gated the same way (#51, Coder/Linter) ---
            evf = lambda tool, path: evaluate_pre(
                {"tool_name": tool, "tool_input": {"file_path": path},
                 "extra": {"task_id": "T1"}}, "memoria-writer", vault)
            check("file write_file allowed zone -> {}", evf("write_file", "inbox/f.md") == {})
            r_fg = evf("write_file", "notes/claims/c.md")
            check("file write_file denied zone -> block", r_fg.get("decision") == "block")
            # to_vault_relative: absolute-under-vault relativized -> gated against lane globs
            abs_claim = str(vault / "notes" / "claims" / "c.md")
            check("to_vault_relative: abs under vault -> relative",
                  to_vault_relative(abs_claim, vault) == "notes/claims/c.md")
            check("file write abs in-vault denied zone -> block",
                  evf("write_file", abs_claim).get("decision") == "block")
            # absolute path OUTSIDE the vault -> None -> not gated (proceeds)
            check("to_vault_relative: abs outside vault -> None",
                  to_vault_relative("/etc/passwd", vault) is None)
            check("file write outside vault -> {} (gate governs vault only)",
                  evf("write_file", "/tmp/external-repo/main.py") == {})

            # pre -> post reversibility roundtrip (paired before/after hash) ------
            (vault / "inbox").mkdir(parents=True, exist_ok=True)
            ev_payload = {"tool_name": "obsidian_put_content",
                          "tool_input": {"filepath": "inbox/round.md"},
                          "extra": {"task_id": "T9", "tool_call_id": "call-xyz"}}
            pre = evaluate_pre(ev_payload, "memoria-writer", vault)
            stash = _pending_file(vault, _stash_key(ev_payload))
            check("pre allow stashes before_hash", pre == {} and stash.is_file())
            # the tool "runs": the file now exists with content
            (vault / "inbox" / "round.md").write_text("answer body", encoding="utf-8")
            post = evaluate_post(ev_payload, "memoria-writer", vault)
            # A missing audit file means complete_write failed (swallowed above); report
            # it as a clear check instead of crashing the whole suite on read_text().
            audit_file = vault / "system" / "logs" / "audit.jsonl"
            check("post wrote the audit log", audit_file.is_file())
            audit_lines = audit_file.read_text(encoding="utf-8").splitlines() if audit_file.is_file() else []
            completes = [json.loads(ln) for ln in audit_lines if json.loads(ln).get("decision") == "write_complete"]
            check("post returns {} (never blocks)", post == {})
            check("post appended a write_complete record", len(completes) == 1)
            check("write_complete pairs before+after", bool(completes and completes[0]["before_hash"] and completes[0]["after_hash"] and completes[0]["before_hash"] != completes[0]["after_hash"]))
            check("post cleaned up the stash", not stash.is_file())

        return t.summary()
    assert _run() == 0
