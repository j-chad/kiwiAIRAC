import re
from enum import Enum
from typing import Optional

from errors import ParseError

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
		elif match := GENERIC_PATTERN.match(page):
			self.section = Section(match.group(1))
			self.subsection = int(match.group(2))
			self.document = int(match.group(3))
			self.page = int(match.group(4))
			self.colour = self._get_colour()
		elif match := AERODROME_PATTERN.match(page):
			self.aerodrome = match.group(1)
			self.subsection = 0
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
