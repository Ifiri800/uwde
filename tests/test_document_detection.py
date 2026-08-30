import pytest

from backend.app.services.documents.detection import (
    detect_document_type,
    supported_document_types,
    supported_extensions,
)
from backend.app.services.documents.errors import (
    UnsupportedDocumentType,
)
from backend.app.services.documents.models import DocumentType


def test_detect_csv_from_extension():
    assert detect_document_type("data.csv") == DocumentType.CSV


def test_detect_xlsx_from_extension():
    assert detect_document_type("data.xlsx") == DocumentType.XLSX


def test_detect_json_from_extension():
    assert detect_document_type("data.json") == DocumentType.JSON


def test_detect_txt_from_extension():
    assert detect_document_type("notes.txt") == DocumentType.TXT


def test_detect_html_from_extension():
    assert detect_document_type("page.html") == DocumentType.HTML


def test_detect_pdf_from_extension():
    assert detect_document_type("report.pdf") == DocumentType.PDF


def test_detect_docx_from_extension():
    assert detect_document_type("report.docx") == DocumentType.DOCX


def test_detect_htm_from_extension():
    assert detect_document_type("page.htm") == DocumentType.HTML


def test_detect_from_media_type_when_extension_is_unknown():
    assert (
        detect_document_type(
            "uploaded.data",
            "application/json",
        )
        == DocumentType.JSON
    )


def test_media_type_parameters_are_ignored():
    assert (
        detect_document_type(
            "uploaded.data",
            "text/csv; charset=utf-8",
        )
        == DocumentType.CSV
    )


def test_extension_takes_priority_over_media_type():
    assert (
        detect_document_type(
            "data.csv",
            "application/json",
        )
        == DocumentType.CSV
    )


def test_unsupported_extension_and_media_type_raise():
    with pytest.raises(UnsupportedDocumentType):
        detect_document_type("data.exe")


def test_missing_filename_raises():
    with pytest.raises(ValueError):
        detect_document_type("")


def test_supported_extensions_are_available():
    extensions = supported_extensions()

    assert ".csv" in extensions
    assert ".xlsx" in extensions
    assert ".json" in extensions
    assert ".txt" in extensions
    assert ".html" in extensions
    assert ".pdf" in extensions
    assert ".docx" in extensions


def test_supported_document_types_are_available():
    document_types = supported_document_types()

    assert DocumentType.CSV in document_types
    assert DocumentType.XLSX in document_types
    assert DocumentType.JSON in document_types
    assert DocumentType.TXT in document_types
    assert DocumentType.HTML in document_types
    assert DocumentType.PDF in document_types
    assert DocumentType.DOCX in document_types
