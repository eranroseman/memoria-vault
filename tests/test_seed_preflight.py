from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.product.seed_corpus import load_seed_manifest
from memoria_vault.runtime import seed_install
from memoria_vault.runtime.operations import load_operation_policy, require_allowed_network

pytestmark = pytest.mark.live


def _recording_opener(requested: list[str]) -> Callable[[str], Any]:
    def opener(url: str) -> Any:
        requested.append(url)
        return seed_install._default_opener(url)

    return opener


def _recording_authorizer(policy: dict[str, Any], authorized: list[str]) -> Callable[[str], None]:
    def authorize(url: str) -> None:
        authorized.append(url)
        require_allowed_network(policy, url)

    return authorize


def test_shipped_seed_endpoints_are_live_and_policy_authorized() -> None:
    policy = load_operation_policy(Path(), "seed-install")
    report = []
    for row in load_seed_manifest():
        requested: list[str] = []
        authorized: list[str] = []

        try:
            raw = seed_install.resolve_fetch(
                row,
                opener=_recording_opener(requested),
                authorize_url=_recording_authorizer(policy, authorized),
            )
            report.append(
                {
                    "id": row["id"],
                    "requested_urls": requested,
                    "pdf_admitted": raw.startswith(b"%PDF-"),
                    "error": "",
                }
            )
        except Exception as exc:  # noqa: BLE001 -- report every provider failure before asserting.
            report.append(
                {
                    "id": row["id"],
                    "requested_urls": requested,
                    "pdf_admitted": False,
                    "error": seed_install._bounded_seed_error(exc),
                }
            )
        assert requested == authorized

    print(json.dumps(report, indent=2, sort_keys=True))
    assert all(row["pdf_admitted"] for row in report), json.dumps(report, indent=2)
