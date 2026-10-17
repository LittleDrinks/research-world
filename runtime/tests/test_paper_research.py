import importlib.util
from pathlib import Path
import shutil
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / '.agents/skills/paper-research/scripts/paper.py'
spec = importlib.util.spec_from_file_location('paper', SCRIPT)
paper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paper)


def test_citations_require_exact_quote_page_and_source():
    document = {'source_sha256': 'abc', 'pages': [
        {'page': 1, 'text': 'Only valid under condition A.', 'status': 'extracted'}]}
    valid = {'source_sha256': 'abc', 'page': 1, 'quote': 'under condition A'}
    candidates = [valid, {**valid, 'page': 2}, {**valid, 'source_sha256': 'def'},
                  {**valid, 'quote': 'universally valid'}, {**valid, 'quote': ''}]
    assert [c['quote_verified'] for c in paper.verify(document, candidates)] == [True, False, False, False, False]


def text_pdf(path):
    stream = b'BT /F1 20 Tf 50 700 Td (Evidence requires careful review.) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream']
    data, offsets = b'%PDF-1.4\n', [0]
    for index, value in enumerate(objects, 1):
        offsets.append(len(data))
        data += f'{index} 0 obj\n'.encode() + value + b'\nendobj\n'
    xref = len(data)
    data += b'xref\n0 6\n0000000000 65535 f \n'
    data += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    path.write_bytes(data + f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode())


@pytest.mark.skipif(not shutil.which('tesseract') or not shutil.which('pdftoppm'), reason='requires Poppler and Tesseract')
def test_real_native_and_scanned_pdf_extraction(tmp_path):
    from PIL import Image
    native = tmp_path / 'native.pdf'
    text_pdf(native)
    extracted = paper.extract(native)
    assert 'Evidence requires careful review.' in extracted['pages'][0]['text']
    assert extracted['pages'][0]['method'] == 'poppler'
    subprocess.run(['pdftoppm', '-singlefile', '-r', '150', '-png', str(native), str(tmp_path / 'scan')], check=True)
    with Image.open(tmp_path / 'scan.png') as image:
        image.convert('RGB').save(tmp_path / 'scan.pdf', resolution=150)
    scanned = paper.extract(tmp_path / 'scan.pdf')
    assert 'Evidence requires careful review.' in scanned['pages'][0]['text']
    assert scanned['pages'][0]['method'] == 'tesseract'
    assert scanned['source_sha256'] != extracted['source_sha256']


def test_failed_page_preserves_coverage_gap(monkeypatch):
    def fail(*args):
        raise subprocess.TimeoutExpired('pdftotext', 120)
    monkeypatch.setattr(paper, 'run', fail)
    assert paper.page_text('input.pdf', 2, 'eng', False) == {
        'page': 2, 'text': '', 'method': 'failed', 'status': 'unreadable'}


def test_forced_ocr_bypasses_broken_text_layer(monkeypatch):
    def fail(*args):
        raise AssertionError('Forced OCR must not invoke text extraction')
    monkeypatch.setattr(paper, 'run', fail)
    monkeypatch.setattr(paper, 'ocr', lambda *args: 'Readable scanned evidence')
    result = paper.page_text('damaged-text.pdf', 1, 'eng', True)
    assert result == {'page': 1, 'text': 'Readable scanned evidence',
                      'method': 'tesseract', 'status': 'extracted'}
