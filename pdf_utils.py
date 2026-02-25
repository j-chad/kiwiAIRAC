import pathlib

from pypdf import PdfReader


def get_pdf_width(path: pathlib.Path, check_all = True) -> int:
	"""Returns the width of the PDF pages, and checks that all pages have the same width."""
	reader = PdfReader(path)
	width = reader.pages[0].mediabox.width

	if check_all and len(reader.pages) > 1:
		for page in reader.pages[1:]:
			if page.mediabox.width != width:
				raise ValueError("PDF pages have different widths, which is not supported")

	return width
