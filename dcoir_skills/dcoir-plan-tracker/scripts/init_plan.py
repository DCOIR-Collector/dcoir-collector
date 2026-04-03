#!/usr/bin/env python3
"""Create a local starter plan folder for dcoir-plan-tracker.

This script is a deterministic scaffold generator. It is useful for previewing the exact
markdown and JSON contents before writing them to GitHub through the connector lane.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from plan_templates import build_plan_id, make_empty_plan_state, today_yyyymmdd, write_plan_folder


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--date", default=today_yyyymmdd())
    parser.add_argument("--owner", default="assistant")
    parser.add_argument("--output-root", default=".")
    args = parser.parse_args()

    plan_id = build_plan_id(args.date, args.slug)
    plan = make_empty_plan_state(plan_id, args.title, args.objective, owner=args.owner)
    plan_dir = Path(args.output_root) / plan_id
    write_plan_folder(plan_dir, plan)
    print(plan_id)
    print(plan_dir)


if __name__ == "__main__":
    main()
