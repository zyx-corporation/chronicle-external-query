#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from chronicle_external_query.release import build_release_notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--release-date", default=str(date.today()))
    parser.add_argument("--output")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    notes = build_release_notes(
        version=args.version,
        release_date=args.release_date,
        repo_root=repo_root,
    )
    if args.output:
        Path(args.output).write_text(notes, encoding="utf-8")
    else:
        print(notes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
