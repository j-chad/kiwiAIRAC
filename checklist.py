import pathlib
import re
import tempfile

import camelot
import requests
from camelot.core import Table, TableList
from pypdf import PdfReader

# Where to download the checklist PDF from.
CHECKLIST_URL = 'https://www.aip.net.nz/assets/AIP/General-GEN/0-GEN/GEN_0.4.pdf'

# Each page in the combined table section of the checklist PDF has a header like "GEN 0.4 - 1", "GEN 0.4 - 2", etc.
HEADER_NUM_RE = re.compile(r"GEN 0.4 - (\d+)")

# If a page has less than this many lines,
# it's probably a blank page or a page with just a header/footer, so we can skip it.
BLANK_PAGE_LINES_THRESHOLD = 5

# Define the table areas for camelot to improve parsing accuracy.
# There are two tables on each page. The spacing is slightly shifted between odd and even pages.
# Additionally, the first page has a header that takes up more space than the other pages, so we need to adjust for that as well.
HEADER_BOTTOM = 550
HEADER_BOTTOM_FIRST_PAGE = 510
FOOTER_TOP = 30
TABLE_SEPARATOR_ODD = 220
TABLE_SEPARATOR_EVEN = 193

class ParseError(Exception):
	pass


class Checklist:
	@staticmethod
	def download() -> 'Checklist':
		response = requests.get(CHECKLIST_URL)
		response.raise_for_status()

		with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
			f.write(response.content)
			pdf_path = pathlib.Path(f.name)
			return Checklist(pdf_path)

	def __init__(self, pdf_path: pathlib.Path):
		self.path = pdf_path
		self.width = self._get_pdf_width()
		pages = self._get_combined_pages()
		tables = self._parse_tables(pages)

	def _get_pdf_width(self) -> int:
		reader = PdfReader(self.path)
		width = reader.pages[0].mediabox.width
		for page in reader.pages[1:]:
			if page.mediabox.width != width:
				raise ParseError("PDF pages have different widths, which is not supported")
		return width

	def _get_table_areas(self, odd: bool, first = False) -> list[str]:
		if first and not odd:
			raise ParseError("First page is odd")

		top = HEADER_BOTTOM_FIRST_PAGE if first else HEADER_BOTTOM
		separator = TABLE_SEPARATOR_ODD if odd else TABLE_SEPARATOR_EVEN
		return [
			f"0,{top},{separator},{FOOTER_TOP}",
			f"{separator},{top},{self.width},{FOOTER_TOP}"
		]

	def _parse_tables(self, pages: list[int]) -> list[Table]:
		tables: list[Table] = []

		pages = sorted(pages)
		if pages[0] == 1:
			first_page = self._parse_tables_with_areas([pages.pop(0)], self._get_table_areas(odd=True, first=True))
			tables.extend(first_page)

		odd_page_numbers = [p for p in pages if p % 2 == 1]
		odd_pages = self._parse_tables_with_areas(odd_page_numbers, self._get_table_areas(odd=True))
		tables.extend(odd_pages)

		even_page_numbers = [p for p in pages if p % 2 == 0]
		even_pages = self._parse_tables_with_areas(even_page_numbers, self._get_table_areas(odd=False))
		tables.extend(even_pages)

		print(f"Parsed {len(tables)} tables from the PDF with accuracy: {[t.parsing_report['accuracy'] for t in tables]}")

		self._debug_camelot(tables[0])

	def _parse_tables_with_areas(self, pages: list[int], areas: list[str]) -> TableList:
		pages_str = ",".join(str(p) for p in pages)
		tables = camelot.read_pdf(self.path, pages=pages_str, flavor='network', table_areas=areas, parallel=True)

		if tables.n != len(pages) * len(areas):
			raise ParseError(f"Expected to find {len(pages) * len(areas)} tables, but found {tables.n}")

		for table in tables:
			if table.parsing_report['accuracy'] < 90:
				raise ParseError(f"Low parsing accuracy: {table.parsing_report['accuracy']}%")

		return tables


	def _debug_camelot(self, table: Table):
		camelot.plot(table).show()

	"""
	Finds the page numbers of the combined table in the checklist PDF.

	The checklist PDF contains 3 sections:
	* Combined table (All Volumes)
	* Volume 2 & 3
	* Volume 4

	We only care about the combined table, which contains all the files that need to be updated.
	The other tables are just subsets of the combined table, so we can ignore them.
	"""
	def _get_combined_pages(self) -> list[int]:
		reader = PdfReader(self.path)
		result: list[int] = []

		for page_num, page in enumerate(reader.pages, start=1):
			text = page.extract_text()
			if text is None or text.strip() == "":
				raise ParseError(f"Failed to extract text from page {page_num}")

			lines = text.strip().splitlines()
			if not lines:
				raise ParseError(f"No lines found on page {page_num}")
			if len(lines) < BLANK_PAGE_LINES_THRESHOLD:
				continue

			header = lines[0]
			match = HEADER_NUM_RE.search(header)
			if match is None:
				raise ParseError(f"Unexpected header format on page {page_num}: {header}")

			header_num = int(match.group(1))
			# volumes 2 & 3 table starts at GEN 0.4 - 200, so we can stop once we reach that.
			if header_num >= 200:
				return result

			result.append(page_num)


if __name__ == '__main__':
	path = pathlib.Path('test/GEN_0.4.pdf')
	checklist = Checklist(path)
