#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys

DIR_NAMES = {"__pycache__"}
FILE_NAMES = {".DS_Store"}
FILE_SUFFIXES = {".pyc", ".pyo"}


def collect(root: Path):
    hits = []
    for path in root.rglob('*'):
        name = path.name
        if path.is_dir() and name in DIR_NAMES:
            hits.append(path)
        elif path.is_file() and (name in FILE_NAMES or path.suffix in FILE_SUFFIXES):
            hits.append(path)
    return sorted(hits)


def remove(paths):
    removed = []
    for path in sorted(paths, key=lambda p: len(p.parts), reverse=True):
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        removed.append(path)
    return removed


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--clean', action='store_true')
    ap.add_argument('paths', nargs='+')
    args = ap.parse_args()

    all_hits = []
    for raw in args.paths:
        root = Path(raw).resolve()
        if not root.exists():
            print(f'MISSING\t{root}')
            return 2
        hits = collect(root)
        if args.clean:
            removed = remove(hits)
            for item in removed:
                print(f'REMOVED\t{item}')
            hits = collect(root)
        all_hits.extend(hits)

    if all_hits:
        for item in all_hits:
            print(f'RESIDUE\t{item}')
        return 1

    print('CLEAN')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
