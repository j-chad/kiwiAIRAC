import uuid
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter

from aip_page import AIPPage

def stitch_pdfs(pdf_paths: Iterable[Path], output_path: Path) -> Path:
	writer = PdfWriter()

	for pdf_path in pdf_paths:
		with open(pdf_path, 'rb') as pdf_file:
			reader = PdfReader(pdf_file)
			for page in reader.pages:
				writer.add_page(page)

	with open(output_path, 'wb') as output_pdf_file:
		writer.write(output_pdf_file)

	return output_path

def extract_pages(pdf_path: Path, pages: Iterable[AIPPage], output_dir: Path) -> Path:
	if not output_dir.is_dir():
		raise NotADirectoryError(pdf_path)

	output_pdf_path = output_dir / f'{uuid.uuid7()}.pdf'

	writer = PdfWriter()
	with open(pdf_path, 'rb') as pdf_file:
		reader = PdfReader(pdf_file)

		for page in pages:
			if not page.available:
				continue
			writer.add_page(reader.pages[page.page_number - 1])

		with open(output_pdf_path, 'wb') as output_pdf_file:
			writer.write(output_pdf_file)


