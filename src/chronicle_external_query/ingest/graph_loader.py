from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_graph_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("graph.json must decode to an object")
    return payload
