import datetime
import pathlib
import re
from itertools import zip_longest
from typing import Iterator

import camelot
import pandas as pd
from pypdf import PdfReader

from aip_page import AIPPage, categorise_pages
from download import downloader, DownloadJob, RichProgressReporter, RichBatchProgressReporter
from errors import ParseError
from models import Volume, Subscription

# Where to download the checklist PDF from.
CHECKLIST_JOB = DownloadJob(url='https://www.aip.net.nz/assets/AIP/General-GEN/0-GEN/GEN_0.4.pdf', content_types=['application/pdf'])

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

# If table parsing accuracy is below this threshold a ParseError will be raised.
MIN_TABLE_PARSE_ACCURACY = 95

# Page Name
PAGE_REGEX = re.compile(r"Blank|[a-zA-Z ]+\d+(?:-\d+)?(?:\.\d+)?(?:-\d+)?[A-Z]?")

# Date Format
DATE_FORMAT = "%d %b %y"
DATE_REGEX = re.compile(r"\d{1,2} [A-Za-z]{3} \d{2}")


class Checklist:
	@staticmethod
	async def fetch() -> 'Checklist':
		"""Downloads the checklist PDF from the specified URL and returns a Checklist instance."""
		with RichProgressReporter() as progress:
			checklist_path = await downloader.download(CHECKLIST_JOB, progress=progress)
		return Checklist(checklist_path)

	def __init__(self, pdf_path: pathlib.Path):
		"""Initialises the Checklist by parsing the specified PDF file."""
		self._path = pdf_path
		self._width = self._get_pdf_width()
		pages = self._get_combined_pages()

		self._df = self._extract_tables(pages)
		self._mask = pd.Series([True] * len(self._df))

	def __len__(self) -> int:
		"""Returns the number of rows in the checklist."""
		return len(self._df_filtered)

	def __iter__(self) -> Iterator[AIPPage]:
		"""Iterates over the rows in the checklist, yielding an AIPPage for each row."""
		return (AIPPage(page_number) for page_number in self._df_filtered["Page No"])

	def volumes(self, volumes: Subscription | set[Volume]) -> 'Checklist':
		"""Filter the checklist to only include rows that are relevant to the specified volumes."""
		if isinstance(volumes, Subscription):
			volumes = volumes.value

		self._mask &= self._df["Volume"].apply(lambda v: not v.isdisjoint(volumes))
		return self

	def effective_after(self, date: datetime.date) -> 'Checklist':
		"""Filter the checklist to only include rows with an effective date after the specified date."""
		self._mask &= self._df["Effective"] > pd.to_datetime(date)
		return self

	def _get_pdf_width(self) -> int:
		"""Returns the width of the PDF pages, and checks that all pages have the same width."""
		reader = PdfReader(self._path)
		width = reader.pages[0].mediabox.width
		for page in reader.pages[1:]:
			if page.mediabox.width != width:
				raise ParseError("PDF pages have different widths, which is not supported")
		return width

	def _get_table_areas(self, odd: bool, first = False) -> list[str]:
		"""
		Returns the areas of a page where tables are located

		Each area is defined as a string in the format "x1,y1,x2,y2", where (x1, y1) is the top-left corner and (x2, y2) is the bottom-right corner of the area.
		The areas are different for odd and even pages, and the first page has a different header size
		"""
		if first and not odd:
			raise ParseError("First page is odd")

		top = HEADER_BOTTOM_FIRST_PAGE if first else HEADER_BOTTOM
		separator = TABLE_SEPARATOR_ODD if odd else TABLE_SEPARATOR_EVEN
		return [
			f"0,{top},{separator},{FOOTER_TOP}",
			f"{separator},{top},{self._width},{FOOTER_TOP}"
		]

	def _extract_tables(self, pages: list[int]) -> pd.DataFrame:
		"""Extracts tables from the specified pages in the checklist PDF."""
		tables: list[pd.DataFrame] = []

		pages = sorted(pages)
		if pages[0] == 1:
			first_page = self._extract_tables_from_area([pages.pop(0)], self._get_table_areas(odd=True, first=True))
			tables.extend(first_page)

		odd_page_numbers = [p for p in pages if p % 2 == 1]
		odd_pages = self._extract_tables_from_area(odd_page_numbers, self._get_table_areas(odd=True))

		even_page_numbers = [p for p in pages if p % 2 == 0]
		even_pages = self._extract_tables_from_area(even_page_numbers, self._get_table_areas(odd=False))

		for even_df, odd_df in zip_longest(even_pages, odd_pages):
			if even_df is not None:
				tables.append(even_df)
			if odd_df is not None:
				tables.append(odd_df)

		return pd.concat(tables, ignore_index=True)

	def _extract_tables_from_area(self, pages: list[int], areas: list[str]) -> Iterator[pd.DataFrame]:
		"""Extracts tables from the specified pages and areas using camelot."""
		pages_str = ",".join(str(p) for p in pages)
		tables = camelot.read_pdf(self._path, pages=pages_str, flavor='network', table_areas=areas, parallel=True)

		if tables.n != len(pages) * len(areas):
			raise ParseError(f"Expected to find {len(pages) * len(areas)} tables, but found {tables.n}")

		for table in tables:
			if table.parsing_report['accuracy'] < MIN_TABLE_PARSE_ACCURACY:
				raise ParseError(f"Low parsing accuracy: {table.parsing_report['accuracy']}%")

		# sort tables by their x-coordinate (i.e. left to right)
		tables = sorted(tables, key = lambda t: t._bbox[0])

		# normalise the tables into a consistent format
		tables = map(lambda t: self._normalise_df(t.df), tables)

		return tables

	@property
	def _df_filtered(self) -> pd.DataFrame:
		"""Returns the filtered DataFrame based on the current mask."""
		return self._df[self._mask]

	@staticmethod
	def _normalise_df(df: pd.DataFrame) -> pd.DataFrame:
		"""Normalises the extracted table DataFrame

		parsing the table is a bit error-prone, so this function applies some heuristics to fix common parsing errors
		and normalise the data into a more consistent format.
		"""
		# drop the header row
		df.columns = df.iloc[0]
		df.columns = df.columns.str.replace(r"\s+", " ",
											regex=True).str.strip()  # normalise whitespace for easier comparison
		df = df.drop(index=0).reset_index(drop=True)

		# fix common parsing errors
		if df.shape[1] == 2:
			# sometimes the "Effective" column is merged with the "Page No" column
			if df.columns.equals(pd.Index(["Page No Effective", "Volume"])):
				# use PAGE_REGEX & DATE_REGEX to split the "Page No" and "Effective" values into separate columns
				df[["Page No", "Effective"]] = df["Page No Effective"].str.extract(
					f"({PAGE_REGEX.pattern})(?:\\s+({DATE_REGEX.pattern}))?")
				df = df.drop(columns=["Page No Effective"])

		if df.shape[1] != 3:
			raise ParseError(f"Expected 3 columns, found {df.shape[1]}")

		if not set(df.columns) == {"Page No", "Effective", "Volume"}:
			raise ParseError(f"Unexpected column headers: {df.iloc[0].tolist()}")

		# Remove section headers
		df = df[~(df["Page No"].str.contains(r"^[A-Za-z\s]+$") & (df["Effective"].str.strip() == "") & (
				df["Volume"].str.strip() == ""))].reset_index(drop=True)

		# Convert volume string into set of volumes
		df["Volume"] = df["Volume"].str.findall(r"[1234]").apply(lambda x: set(map(lambda v: Volume(int(v)), x)))

		# Convert date
		df["Effective"] = pd.to_datetime(df["Effective"], format=DATE_FORMAT)

		return df

	def _get_combined_pages(self) -> list[int]:
		"""
		Finds the page numbers of the combined table in the checklist PDF.

		The checklist PDF contains 3 sections:
		* Combined table (All Volumes)
		* Volume 2 & 3
		* Volume 4

		We only care about the combined table, which contains all the files that need to be updated.
		The other tables are just subsets of the combined table, so we can ignore them.
		"""
		reader = PdfReader(self._path)
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

		return result

async def _main():
	checklist_inst = await Checklist.fetch()
	checklist_inst.volumes(Subscription.VISUAL).effective_after(datetime.date(2024, 6, 1))

	categorise_pages(checklist_inst)

	jobs = [DownloadJob(url=page.url, content_types=['application/pdf']) for page in checklist_inst if page.url is not None]

	with RichBatchProgressReporter(len(jobs)) as progress:
		await downloader.download_many(jobs, progress=progress)

if __name__ == '__main__':
	import asyncio
	raise SystemExit(asyncio.run(_main()))

