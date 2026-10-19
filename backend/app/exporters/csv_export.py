"""CSV exporter with UTF-8 BOM."""

from __future__ import annotations

import csv
import io

from app.exporters.common import CSV_HEADERS, review_row
from app.models import Review

BOM = "\ufeff"


def export_csv(reviews: list[Review]) -> bytes:
    buffer = io.StringIO()
    buffer.write(BOM)
    writer = csv.DictWriter(buffer, fieldnames=CSV_HEADERS, lineterminator="\n")
    writer.writeheader()
    for review in reviews:
        writer.writerow(review_row(review))
    return buffer.getvalue().encode("utf-8")
