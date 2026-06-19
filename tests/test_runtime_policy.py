"""The packaged runtime policy primitives remain the canonical implementation."""

import pytest

from memoria.runtime.policy import (
    glob_to_regex,
    normalize_path,
    path_matches,
    within_scope,
)


def test_normalize_path_rejects_escape_and_collapses_segments():
    assert normalize_path("./a/b/../c") == "a/c"
    with pytest.raises(ValueError):
        normalize_path("../../etc/passwd")


def test_lane_globs_and_scopes_share_one_semantics():
    assert path_matches("projects/demo/code/main.py", ["projects/*/code/**"])
    assert not path_matches("projects/demo/draft.md", ["projects/*/code/**"])
    assert within_scope("projects/demo/code", ["projects/*/code/"])
    assert glob_to_regex("**") == "^.*$"
