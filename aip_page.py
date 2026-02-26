import re
from enum import Enum
from typing import Optional

from errors import ParseError, DocumentAccessError

GENERIC_PATTERN = re.compile(r"([a-zA-Z]+) (\d+)\.(\d+)-(\d+)")
AERODROME_PATTERN = re.compile(r"(NZ[A-Z]{2}) AD 2-(\d+)(?:\.(\d+)(Y?))?")
UNAVAILABLE_PATTERN = re.compile(r"([a-zA-Z ]+) (\d+)-(\d+)")

# Where the emergency document is located in the En Route section
EMERGENCY_DOCUMENT = 15

class PageColour(Enum):
	YELLOW = 'Y'
	PINK = 'P'

class Section(Enum):
	BLANK = 'Blank'
	TITLE = 'Title'
	GENERAL = 'GEN'
	EN_ROUTE = 'ENR'
	AERODROMES = 'AD'
	AERODROME_CHARTS = 'AD 2'


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
	Section.EN_ROUTE: BASE_URL + "En-route-ENR/{subsection}-{subsection_name}/ENR_{subsection}.{document}.pdf",
	Section.AERODROMES: BASE_URL + "Aerodromes-AD1/{subsection_name}/AD_{subsection}.{document}.pdf"
}
AERODROME_URL = BASE_URL + "Aerodromes-AD1/AERODROMES/{aerodrome}_AD2.pdf"

class AIPPage:
	page: str

	section: Section
	subsection: int
	document: int
	page: int
	colour: Optional[PageColour] = None
	aerodrome: Optional[str] = None

	# some documents can not be found online
	available: bool = True

	def __init__(self, page: str):
		self.page = page

		if page == Section.BLANK.value:
			self.section = Section.BLANK
			self.subsection = 0
			self.document = 0
			self.page = 0
			self.available = False
		elif match := GENERIC_PATTERN.match(page):
			self.section = Section(match.group(1))
			self.subsection = int(match.group(2))
			self.document = int(match.group(3))
			self.page = int(match.group(4))
			self.colour = self._get_colour()
		elif match := AERODROME_PATTERN.match(page):
			self.aerodrome = match.group(1)
			self.subsection = 2
			chart = match.group(3)
			if chart is None:
				self.section = Section.AERODROMES
				self.document = 0
				self.page = int(match.group(2))
			else:
				self.section = Section.AERODROME_CHARTS
				self.document = int(match.group(2))
				self.page = int(chart)
				self.colour = self._get_colour(match.group(4))
		elif match := UNAVAILABLE_PATTERN.match(page):
			self.section = Section(match.group(1))
			self.subsection = 0
			self.document = int(match.group(2))
			self.page = int(match.group(3))
			self.available = False
		else:
			raise ParseError(f"Invalid page format: {page}")

	def __str__(self):
		return self.page

	def __repr__(self):
		return f"AIPPage(page='{self.page}')"

	def _get_colour(self, flags_str: str = "") -> Optional[PageColour]:
		"""Determines the colour of the page

		- If the page has a "Y" flag, it is yellow.
		- If the page is the emergency document in the En Route section, it is pink.
		- Otherwise, it is white (None).
		"""
		if flags_str == "Y":
			return PageColour.YELLOW
		elif self.section == Section.EN_ROUTE and self.document == EMERGENCY_DOCUMENT:
			return PageColour.PINK
		return None

	def _get_url(self) -> Optional[str]:
		"""Constructs the URL for the page based on its section, subsection, document, and page numbers.

		- If the page is not available, raises a DocumentAccessError.
		- If the URL is not guessable based on the page information, returns None.
		"""
		if not self.available:
			raise DocumentAccessError(f"Page {self.page} is not available online")

		if self.section == Section.AERODROMES and self.aerodrome is not None:
			return AERODROME_URL.format(aerodrome=self.aerodrome)

		section_name = SUBSECTION_NAMES.get(self.section, {}).get(self.subsection)
		if section_name is None:
			return None

		url_pattern = SECTION_URL_PATTERNS.get(self.section)
		if url_pattern is None:
			return None

		return url_pattern.format(subsection=self.subsection, subsection_name=section_name, document=self.document)



