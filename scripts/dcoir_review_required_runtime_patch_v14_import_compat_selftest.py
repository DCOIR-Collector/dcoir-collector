#!/usr/bin/env python3
"""Import-compatibility self-test for DCOIR Review v14.

This covers the #340 workflow crash shape: the live v13 module did not expose
some helper names that v14 preserved unconditionally at import time.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import dcoir_review_required_runtime_patch_v13 as v13


def main() -> None:
    for name in ("_render_integrity_errors", "_rendered_comment_has_integrity_problem"):
        if hasattr(v13, name):
            delattr(v13, name)

    if not hasattr(v13, "_rendered_comment_has_problem"):
        v13._rendered_comment_has_problem = lambda _rendered, _finding: False

    v14 = importlib.import_module("dcoir_review_required_runtime_patch_v14")

    assert v14._render_integrity_errors([], {}) == []
    metadata = v14._augment_metadata([], [], [], SimpleNamespace(max_inline_comments=12), {"selected_keys": []})
    assert metadata["version"] == "v14"

    module = SimpleNamespace(base=None, hardened=None)
    v14.apply_pareto_context_module(module)
    assert v13._rendered_comment_has_problem is v14._rendered_comment_has_integrity_problem
    assert v13._rendered_comment_has_integrity_problem is v14._rendered_comment_has_integrity_problem

    print("dcoir_review_required_runtime_patch_v14_import_compat_selftest passed")


if __name__ == "__main__":
    main()
