"""Extract original PDF text for review; never infer coordinates or status."""
import argparse
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description='Extract municipal PDF text for reviewed address import')
parser.add_argument('pdf', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not args.pdf.read_bytes().startswith(b'%PDF'):
    parser.error('Input is not a PDF')
args.output.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', str(args.pdf), str(args.output)], check=True)
print(f'Extracted text to {args.output}. Review Hebrew direction, row boundaries, street names and house numbers before importing. An empty output may require OCR.')
