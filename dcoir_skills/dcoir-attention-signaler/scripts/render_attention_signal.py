#!/usr/bin/env python3
from __future__ import annotations
import argparse

LABELS = {
    'session-start': 'SESSION START',
    'milestone': 'MILESTONE',
    'review': 'REVIEW',
    'complete': 'COMPLETE',
    'action-required': 'ACTION REQUIRED',
    'blocked': 'BLOCKED',
}


def banner(label: str, message: str) -> str:
    border = '=' * 46
    return f"**{border}**\n**{label}: {message.upper()}**\n**{border}**"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--signal-class', required=True, choices=sorted(LABELS))
    ap.add_argument('--placement', required=True, choices=['header', 'footer', 'dual'])
    ap.add_argument('--message', required=True)
    args = ap.parse_args()
    text = banner(LABELS[args.signal_class], args.message.strip())
    if args.placement == 'header':
        print(f"[header]\n{text}")
    elif args.placement == 'footer':
        print(f"[footer]\n{text}")
    else:
        print(f"[header]\n{text}\n\n[footer]\n{text}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
