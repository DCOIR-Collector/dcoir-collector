#!/usr/bin/env python3
"""Explicit DCOIR Review entrypoint.

This wrapper applies connector-safe runtime patches before invoking the large
Pareto reviewer script. The workflow should call this file directly.
"""

from __future__ import annotations

import dcoir_review_required_runtime_patch_v2
import dcoir_review_required_runtime_patch_v3
import dcoir_review_required_runtime_patch_v4_apply
import dcoir_review_required_runtime_patch_v5_apply
import dcoir_review_required_runtime_patches
import dcoir_review_runtime_patches
import dcoir_review_strict_runtime_patches
import openrouter_pr_review_pareto_context


def main() -> None:
    dcoir_review_runtime_patches.apply_pareto_context_module(openrouter_pr_review_pareto_context)
    dcoir_review_strict_runtime_patches.apply_pareto_context_module(openrouter_pr_review_pareto_context)
    dcoir_review_required_runtime_patches.apply_pareto_context_module(openrouter_pr_review_pareto_context)
    dcoir_review_required_runtime_patch_v2.apply_pareto_context_module(openrouter_pr_review_pareto_context)
    dcoir_review_required_runtime_patch_v3.apply_pareto_context_module(openrouter_pr_review_pareto_context)
    dcoir_review_required_runtime_patch_v4_apply.apply_pareto_context_module(openrouter_pr_review_pareto_context)
    dcoir_review_required_runtime_patch_v5_apply.apply_pareto_context_module(openrouter_pr_review_pareto_context)
    openrouter_pr_review_pareto_context.main()


if __name__ == "__main__":
    main()
