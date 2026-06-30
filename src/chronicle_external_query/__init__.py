"""External query runtime scaffolding for Chronicle bundles."""

from .ingest.handoff_loader import HandoffBundle, HandoffLoader

__all__ = ["HandoffBundle", "HandoffLoader"]
