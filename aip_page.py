import dataclasses
import re
from enum import Enum
from typing import Optional, Iterable

import aerodromes
from errors import ParseError, DocumentAccessError

GENERIC_PATTERN = re.compile(r"([a-zA-Z]+) (\d+)\.(\d+)-(\d+)")
AERODROME_CHART_PAGE_IDENTIFIER_PATTERN = re.compile(r"(\d+)\.(\d+)([YG]?)")
AERODROME_PATTERN = re.compile(r"(NZ[A-Z]{2}) AD 2-(\d+)(?:\.(\d+)([YG]?))?")
UNAVAILABLE_PATTERN = re.compile(r"([a-zA-Z ]+) (\d+)-(\d+)")

# Where the emergency document is located in the En Route section
EMERGENCY_DOCUMENT = 15

class PageColour(Enum):
	YELLOW = 'Y'
	PINK = 'P'
	GREEN = 'G'

class Section(Enum):
	BLANK = 'Blank'
	TITLE = 'Title'
	GENERAL = 'GEN'
	EN_ROUTE = 'ENR'
	AERODROMES = 'AD'
	AERODROME_CHARTS = 'AD_CHART'


SUBSECTION_NAMES: dict[Section, dict[int, str]] = {
	Section.GENERAL: {
		0: "GEN",
		1: "NATIONAL-REGULATIONS-AND-REQUIREMENTS",
		2: "TABLES-AND-CODES",
		3: "SERVICES",
		4: "CHARGES-FOR-AERODROMES-HELIPORTS-AND-AIR-NAVIGATION-SERVICES"
	},
	Section.EN_ROUTE: {
		0: "ENR",
		1: "GENERAL-RULES-AND-PROCEDURES",
		2: "AIR-TRAFFIC-SUPPORT-SERVICES",
		3: "ATS-ROUTES",
		4: "RADIO-NAVIGATION-AIDS-SYSTEMS",
		5: "NAVIGATION-WARNINGS"
	},
	Section.AERODROMES: {
		0: "AD1",
		1: "AERODROME/HELIPORTS-INTRODUCTION",
	},
}

BASE_URL = "https://www.aip.net.nz/assets/AIP/"
SECTION_URL_PATTERNS: dict[Section, str] = {
	Section.GENERAL: BASE_URL + "General-GEN/{subsection}-{subsection_name}/GEN_{subsection}.{document}.pdf",
	Section.EN_ROUTE: BASE_URL + "En-route-ENR/{subsection}-{subsection_name}/ENR_{subsection}.{document:02d}.pdf",
	Section.AERODROMES: BASE_URL + "Aerodromes-AD1/{subsection_name}/AD_{subsection}.{document:02d}.pdf",
}
AERODROME_URL = BASE_URL + "Aerodromes-AD1/AERODROMES/{aerodrome}_AD2.pdf"

class AIPPage:
	_page_text: str

	section: Section
	subsection: int
	document: int
	page_number: int
	colour: Optional[PageColour] = None
	aerodrome: Optional[str] = None

	# some documents can not be found online
	available: bool = True

	def __init__(self, page: str):
		self._page_text = page

		if page == Section.BLANK.value:
			self.section = Section.BLANK
			self.subsection = 0
			self.document = 0
			self.page_number = 0
			self.available = False
		elif match := GENERIC_PATTERN.match(page):
			self.section = Section(match.group(1))
			self.subsection = int(match.group(2))
			self.document = int(match.group(3))
			self.page_number = int(match.group(4))
			self.colour = self._get_colour()
		elif match := AERODROME_PATTERN.match(page):
			self.aerodrome = match.group(1)
			self.subsection = 2
			chart = match.group(3)
			if chart is None:
				self.section = Section.AERODROMES
				self.document = 0
				self.page_number = int(match.group(2))
			else:
				self.section = Section.AERODROME_CHARTS
				self.document = int(match.group(2))
				self.page_number = int(chart)
				self.colour = self._get_colour(match.group(4))
		elif match := UNAVAILABLE_PATTERN.match(page):
			self.section = Section(match.group(1))
			self.subsection = 0
			self.document = int(match.group(2))
			self.page_number = int(match.group(3))
			self.available = False
		else:
			raise ParseError(f"Invalid page format: {page}")

	def __str__(self):
		return self._page_text

	def __repr__(self):
		return f"AIPPage(page='{self._page_text}', section={self.section})"

	def _get_colour(self, flags_str: str = "") -> Optional[PageColour]:
		"""Determines the colour of the page

		- If the page has a flag indicating a colour, it is that colour (Y for yellow, G for green).
		- If the page is the emergency document in the En Route section, it is pink.
		- Otherwise, it is white (None).
		"""
		try:
			return PageColour(flags_str)
		except ValueError:
			pass

		if self.section == Section.EN_ROUTE and self.document == EMERGENCY_DOCUMENT:
			return PageColour.PINK

		return None

	@property
	def url(self) -> Optional[str]:
		"""Returns the URL for the page purely based on the page information.

		:return: the URL for the page, or None if it cannot be determined lexically
		"""
		if not self.available:
			return None

		# Special case for specific aerodrome documents in the AD section
		if self.section == Section.AERODROMES and self.aerodrome is not None:
			return AERODROME_URL.format(aerodrome=self.aerodrome)

		# Charts
		if self.section == Section.AERODROME_CHARTS and self.aerodrome is not None:
			return self._chart_url()

		section_name = SUBSECTION_NAMES.get(self.section, {}).get(self.subsection)
		if section_name is None:
			return None

		url_pattern = SECTION_URL_PATTERNS.get(self.section)
		if url_pattern is None:
			return None

		return url_pattern.format(
			subsection=self.subsection,
			subsection_name=section_name,
			document=self.document
		)

	def _chart_url(self) -> Optional[str]:
		"""Returns the URL for a chart page, which is based on the aerodrome and document number."""
		if self.aerodrome is None:
			return None

		aerodrome_charts = aerodromes.AERODROME_CHART_DATA.get(self.aerodrome)
		if aerodrome_charts is None:
			return None

		chart_file = None
		for chart in aerodrome_charts:
			match = AERODROME_CHART_PAGE_IDENTIFIER_PATTERN.findall(chart)
			if not match:
				continue

			for doc_num_str, page_num_str, flags in match:
				doc_num = int(doc_num_str)
				page_num = int(page_num_str)
				if doc_num == self.document and page_num == self.page_number:
					chart_file = chart
					break

		if chart_file is not None:
			return BASE_URL + "Aerodrome-Charts/" + chart_file + '.pdf'

		return None

@dataclasses.dataclass(frozen=True)
class Sheet:
	front: AIPPage
	back: Optional[AIPPage] = None

	def __post_init__(self):
		if self.back is not None and self.back.section != Section.BLANK:
			if self.front.colour != self.back.colour:
				raise ValueError(f"Cannot pair pages of different colours: {self.front} and {self.back}")
			if self.front.url != self.back.url:
				raise ValueError(f"Cannot pair pages with different URLs: {self.front} and {self.back}")

# def categorise_pages(pages: Iterable[AIPPage]) -> dict[PageColour, dict[str, list[AIPPage]]]:
# 	"""Collects the AIP pages by colour and URL.
#
# 	Pages that do not have a predictable URL are returned in the second element of the tuple.
# 	"""
# 	collected: dict[PageColour | None, dict[str, list[AIPPage]]] = {}
#
# 	for page in pages:
# 		url = page.url
# 		if url is None:
# 			raise DocumentAccessError(f"Could not determine URL for page: {page}")
#
# 		collected.setdefault(page.colour, {}).setdefault(url, []).append(page)
#
# 	return collected



