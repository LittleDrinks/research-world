"""Page-addressable PDF extraction and exact citation checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, timeout=120,
                          env={**os.environ, 'LC_ALL': 'C'}).stdout.decode('utf-8')


def ocr(path, number, language):
    with tempfile.TemporaryDirectory() as directory:
        image = str(Path(directory) / 'page')
        run('pdftoppm', '-f', str(number), '-l', str(number), '-singlefile',
            '-r', '300', '-png', str(path), image)
        return run('tesseract', image + '.png', 'stdout', '-l', language)


def page_text(path, number, language, force):
    try:
        text = run('pdftotext', '-f', str(number), '-l', str(number), '-layout', str(path), '-')
        method = 'poppler'
        if force or not text.strip():
            text, method = ocr(path, number, language), 'tesseract'
        return {'page': number, 'text': text, 'method': method,
                'status': 'extracted' if text.strip() else 'empty_or_unreadable'}
    except (subprocess.SubprocessError, OSError):
        return {'page': number, 'text': '', 'method': 'failed', 'status': 'unreadable'}


def extract(path, language='eng', force=False):
    data = Path(path).read_bytes()
    with tempfile.TemporaryDirectory() as directory:
        snapshot = Path(directory) / 'source.pdf'
        snapshot.write_bytes(data)
        count = int(re.search(r'^Pages:\s+(\d+)', run('pdfinfo', str(snapshot)), re.M)[1])
        pages = [page_text(snapshot, n, language, force) for n in range(1, count + 1)]
    return {'source_sha256': hashlib.sha256(data).hexdigest(), 'pages': pages,
            'limitations': 'Text extraction is not visual verification of formulas, tables or OCR accuracy.'}


def verify(document, citations):
    pages = {item['page']: item for item in document['pages']}
    results = []
    for citation in citations:
        page = pages.get(citation.get('page'))
        quote = citation.get('quote')
        valid = (citation.get('source_sha256') == document['source_sha256']
                 and page is not None and page['status'] == 'extracted'
                 and isinstance(quote, str) and bool(quote.strip()) and quote in page['text'])
        results.append({**citation, 'quote_verified': bool(valid)})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['extract', 'verify'])
    parser.add_argument('document', type=Path)
    parser.add_argument('--citations', type=Path)
    parser.add_argument('--language', default='eng')
    parser.add_argument('--force-ocr', action='store_true')
    args = parser.parse_args()
    if args.action == 'extract':
        result = extract(args.document, args.language, args.force_ocr)
    else:
        if args.citations is None:
            parser.error('verify requires --citations')
        result = verify(json.loads(args.document.read_text()), json.loads(args.citations.read_text()))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.action == 'verify' and any(not item['quote_verified'] for item in result):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
