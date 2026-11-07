"""Exercise installed document readers through NetMon with private fixtures."""

from types import SimpleNamespace

import docx
import PyPDF2
from PyPDF2.generic import DictionaryObject, NameObject, DecodedStreamObject

from netmon.features import chad_controller


def test_installed_word_reader_extracts_private_fixture(tmp_path):
    path = tmp_path / "fixture.docx"
    document = docx.Document()
    document.add_paragraph("NetMon private Word fixture")
    document.save(path)
    app = SimpleNamespace(tr=lambda key, fallback: fallback)
    assert "NetMon private Word fixture" in chad_controller.extract_docx_text_for_chad(
        app, str(path)
    )


def test_installed_pdf_reader_extracts_private_fixture(tmp_path):
    writer = PyPDF2.PdfWriter()
    writer.add_blank_page(width=300, height=200)
    page = writer.pages[-1]
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
        }
    )
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 10 100 Td (NetMon private PDF fixture) Tj ET")
    page[NameObject("/Contents")] = stream
    path = tmp_path / "fixture.pdf"
    with path.open("wb") as handle:
        writer.write(handle)
    app = SimpleNamespace(tr=lambda key, fallback: fallback)
    assert "NetMon private PDF fixture" in chad_controller.extract_pdf_text_for_chad(
        app, str(path)
    )
