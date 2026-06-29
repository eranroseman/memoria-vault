#!/usr/bin/env python3
"""Helpers for scripts/test-l2.sh."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT / "src", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from memoria_vault.runtime.jsonl import iter_jsonl

DISABLED_TOOLSETS = [
    "browser",
    "clarify",
    "code_execution",
    "computer_use",
    "cronjob",
    "delegation",
    "file",
    "homeassistant",
    "image_gen",
    "memory",
    "messaging",
    "moa",
    "session_search",
    "spotify",
    "terminal",
    "tts",
    "video",
    "video_gen",
    "vision",
    "web",
    "x_search",
    "yuanbao",
]
SMOKE_PLATFORM_TOOLSETS = ["skills", "obsidian"]


def prepare_vault(root: Path, vault: Path) -> None:
    if vault.exists():
        shutil.rmtree(vault)
    shutil.copytree(root / "vault-template", vault, dirs_exist_ok=True)
    (vault / "system/logs").mkdir(parents=True, exist_ok=True)
    audit = vault / "system/logs/audit.jsonl"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.touch()


def write_profile(
    profile_src: Path,
    profile_stage: Path,
    *,
    repo_root: Path,
    vault: Path,
    python: str,
    provider: str,
    model: str,
    base_url: str,
    context_length: int,
) -> None:
    if profile_stage.exists():
        shutil.rmtree(profile_stage)
    profile_stage.mkdir(parents=True)
    shutil.copy2(profile_src / "SOUL.md", profile_stage / "SOUL.md")
    if (profile_src / "skills").is_dir():
        shutil.copytree(profile_src / "skills", profile_stage / "skills")

    distribution = yaml.safe_load((profile_src / "distribution.yaml").read_text(encoding="utf-8"))
    distribution["name"] = "memoria-writer"
    distribution["display_name"] = "Memoria L2 Writer Smoke"
    (profile_stage / "distribution.yaml").write_text(
        yaml.safe_dump(distribution, sort_keys=False),
        encoding="utf-8",
    )

    config = {
        "model": {
            "provider": provider,
            "base_url": base_url,
            "default": model,
            "context_length": context_length,
            "ollama_num_ctx": context_length,
        },
        "mcp_servers": {
            "obsidian": {
                "command": python,
                "args": [
                    str(repo_root / "scripts/l2_obsidian_mcp_shim.py"),
                    "--vault",
                    str(vault),
                ],
                "timeout": 30,
            }
        },
        "platform_toolsets": {
            "cli": SMOKE_PLATFORM_TOOLSETS,
            "cron": SMOKE_PLATFORM_TOOLSETS,
            "api_server": SMOKE_PLATFORM_TOOLSETS,
        },
        "agent": {"tool_use_enforcement": True, "disabled_toolsets": DISABLED_TOOLSETS},
        "terminal": {"cwd": str(vault)},
        "checkpoints": {"enabled": False},
        "plugins": {"enabled": ["memoria-policy-gate"]},
    }
    (profile_stage / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def deploy_policy_plugin(root: Path, profile_dir: Path, profile: str, vault: Path) -> None:
    source = root / "vault-template/.memoria/plugins/memoria-policy-gate"
    target = profile_dir / "plugins/memoria-policy-gate"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "plugin.yaml", target / "plugin.yaml")
    text = (source / "__init__.py").read_text(encoding="utf-8")
    text = text.replace("{{PROFILE}}", profile).replace("{{VAULT_PATH}}", str(vault))
    text = text.replace(
        "if str(_MCP_DIR) not in sys.path:\n    sys.path.insert(0, str(_MCP_DIR))\n",
        "if str(_MCP_DIR) not in sys.path:\n"
        "    sys.path.insert(0, str(_MCP_DIR))\n"
        f"if {str(root / 'src')!r} not in sys.path:\n"
        f"    sys.path.insert(0, {str(root / 'src')!r})\n",
    )
    (target / "__init__.py").write_text(text, encoding="utf-8")


def assert_smoke(vault: Path, artifact_rel: str, audit_before: int) -> None:
    artifact = vault / artifact_rel
    if artifact.exists():
        raise AssertionError(f"direct Obsidian write unexpectedly created {artifact_rel}")

    audit_path = vault / "system/logs/audit.jsonl"
    rows = list(iter_jsonl(audit_path))
    new_rows = rows[audit_before:]
    deny_rows = [
        row
        for row in new_rows
        if row.get("path") == artifact_rel
        and row.get("decision") == "deny"
        and row.get("policy_rule") == "tool-registry.allowlist"
    ]
    if not deny_rows:
        raise AssertionError(f"no tool-registry deny audit row for {artifact_rel}")
    row = deny_rows[-1]
    for field in ("message", "task_id"):
        if not row.get(field):
            raise AssertionError(f"audit row missing {field}: {row}")
    print(f"direct Obsidian write denied: {artifact_rel}")
    print(f"policy-gate deny audit row asserted: task_id={row['task_id']}")


def count_audit_rows(vault: Path) -> int:
    audit = vault / "system/logs/audit.jsonl"
    if not audit.exists():
        return 0
    return len([line for line in audit.read_text(encoding="utf-8").splitlines() if line.strip()])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare-vault")
    prep.add_argument("--root", required=True, type=Path)
    prep.add_argument("--vault", required=True, type=Path)

    profile = sub.add_parser("write-profile")
    profile.add_argument("--profile-src", required=True, type=Path)
    profile.add_argument("--profile-stage", required=True, type=Path)
    profile.add_argument("--repo-root", required=True, type=Path)
    profile.add_argument("--vault", required=True, type=Path)
    profile.add_argument("--python", required=True)
    profile.add_argument("--provider", required=True)
    profile.add_argument("--model", required=True)
    profile.add_argument("--base-url", required=True)
    profile.add_argument("--context-length", required=True, type=int)

    plugin = sub.add_parser("deploy-policy-plugin")
    plugin.add_argument("--root", required=True, type=Path)
    plugin.add_argument("--profile-dir", required=True, type=Path)
    plugin.add_argument("--profile", required=True)
    plugin.add_argument("--vault", required=True, type=Path)

    audit = sub.add_parser("count-audit")
    audit.add_argument("--vault", required=True, type=Path)

    check = sub.add_parser("assert-smoke")
    check.add_argument("--vault", required=True, type=Path)
    check.add_argument("--artifact", required=True)
    check.add_argument("--audit-before", required=True, type=int)

    ns = parser.parse_args(argv)
    if ns.command == "prepare-vault":
        prepare_vault(ns.root, ns.vault)
    elif ns.command == "write-profile":
        write_profile(
            ns.profile_src,
            ns.profile_stage,
            repo_root=ns.repo_root,
            vault=ns.vault,
            python=ns.python,
            provider=ns.provider,
            model=ns.model,
            base_url=ns.base_url,
            context_length=ns.context_length,
        )
    elif ns.command == "deploy-policy-plugin":
        deploy_policy_plugin(ns.root, ns.profile_dir, ns.profile, ns.vault)
    elif ns.command == "count-audit":
        print(count_audit_rows(ns.vault))
    elif ns.command == "assert-smoke":
        assert_smoke(ns.vault, ns.artifact, ns.audit_before)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
