"""Export writers (CSV / XLSX / JSON)."""

from app.exporters.common import export_filename
from app.exporters.csv_export import export_csv
from app.exporters.json_export import export_json
from app.exporters.xlsx_export import export_xlsx
from app.models import ExportFormat, Review, Store


def export_reviews(
    reviews: list[Review],
    fmt: ExportFormat,
    *,
    app_name: str,
    store: Store,
) -> tuple[bytes, str, str]:
    """Return (body, media_type, filename)."""
    if fmt == ExportFormat.CSV:
        return (
            export_csv(reviews),
            "text/csv; charset=utf-8",
            export_filename(app_name, store, "csv"),
        )
    if fmt == ExportFormat.XLSX:
        return (
            export_xlsx(reviews),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            export_filename(app_name, store, "xlsx"),
        )
    if fmt == ExportFormat.JSON:
        return (
            export_json(reviews),
            "application/json; charset=utf-8",
            export_filename(app_name, store, "json"),
        )
    raise ValueError(f"Unsupported export format: {fmt}")
