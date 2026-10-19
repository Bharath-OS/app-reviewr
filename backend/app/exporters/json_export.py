"""JSON exporter."""

from __future__ import annotations

import json

from app.models import Review


def export_json(reviews: list[Review]) -> bytes:
    payload = [r.model_dump(mode="json") for r in reviews]
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
