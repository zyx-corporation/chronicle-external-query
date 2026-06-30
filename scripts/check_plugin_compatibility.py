#!/usr/bin/env python3
from __future__ import annotations

import json

from chronicle_external_query.release import build_plugin_compatibility_report


def main() -> int:
    payload = build_plugin_compatibility_report()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
