"""Exporter unit + route tests."""

from app.exporters import export_reviews
from app.exporters.common import sanitize_cell
from app.exporters.csv_export import BOM, export_csv
from app.exporters.json_export import export_json
from app.exporters.xlsx_export import export_xlsx
from app.models import ExportFormat, Review, Store


def _review(text: str = "Hello", review_id: str = "1") -> Review:
    return Review(
        store=Store.GOOGLE_PLAY,
        app_id="com.example.app",
        app_name="Example App",
        review_id=review_id,
        author="User",
        rating=5,
        title=None,
        text=text,
        date="2024-01-01T00:00:00Z",
        app_version="1.0",
        thumbs_up=0,
        developer_reply=None,
        reply_date=None,
        country="US",
        language="en",
    )


def test_sanitize_formula_injection() -> None:
    assert sanitize_cell("=CMD()") == "'=CMD()"
    assert sanitize_cell("+1234") == "'+1234"
    assert sanitize_cell("-1+1") == "'-1+1"
    assert sanitize_cell("@SUM(A1)") == "'@SUM(A1)"
    assert sanitize_cell("normal") == "normal"


def test_csv_has_bom_and_safe_cells() -> None:
    data = export_csv([_review("=1+1")])
    assert data.startswith(BOM.encode("utf-8"))
    assert b"'=1+1" in data


def test_json_and_xlsx_bytes() -> None:
    reviews = [_review(), _review(review_id="2", text="@risk")]
    assert export_json(reviews).startswith(b"[")
    xlsx = export_xlsx(reviews)
    assert xlsx[:2] == b"PK"  # zip/xlsx magic


def test_export_reviews_filenames() -> None:
    body, media, name = export_reviews(
        [_review()],
        ExportFormat.CSV,
        app_name="Spotify Music",
        store=Store.GOOGLE_PLAY,
    )
    assert media.startswith("text/csv")
    assert name.startswith("appreviewr_spotify-music_play_")
    assert name.endswith(".csv")
    assert body
