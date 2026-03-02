import uuid
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter

from aip_page import AIPPage, PageColour, Section

Url = str
PageGrouping = dict[PageColour | None, dict[Url, tuple[tuple[AIPPage]]]]

class Stitcher:
	"""Utility class for stitching together multiple AIP pages into a single PDF document."""

	_pages: PageGrouping

	def __init__(self, pages: Iterable[AIPPage], *, duplex: bool = True):
		self.duplex = duplex

		self._pages = self._group_pages(pages)

	def _group_pages(self, pages: Iterable[AIPPage]) -> PageGrouping:
		"""Groups the given pages by colour, url and runs of consecutive pages."""
		grouping: PageGrouping = {}
		current_run: list[AIPPage] = []
		for page in pages:
			if page.section == Section.BLANK:
				current_run.append(page)

			url = page.url()
			if url is None:
				raise ValueError(f"Page {page._page_text} does not have a valid URL")

			if page.colour not in grouping:
				grouping[page.colour] = {}

			if url not in grouping[page.colour]:
				grouping[page.colour][url] = []

			grouping[page.colour][url].append(page)

		return grouping


