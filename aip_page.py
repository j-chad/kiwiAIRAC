import re
from enum import Enum
from typing import Optional

GENERIC_PATTERN = re.compile(r"([a-zA-Z]+) (\d+)\.(\d+)-(\d+)")
CHARTS_PATTERN = re.compile(r"(NZ[A-Z]{2}) AD 2-(\d+)\.(\d+)(Y?)")

class PageFlag(Enum):
	YELLOW = 'Y'

class Section(Enum):
	BLANK = 'Blank'
	GENERAL = 'GEN'
	EN_ROUTE = 'ENR'
	AERODROMES = 'AD'
	AERODROME_CHARTS = 'AD 2'

class AIPPage:
	section: Section
	subsection: int
	document: int
	page: int
	aerodrome: Optional[str] = None
	flag: Optional[PageFlag] = None

	def __init__(self, page: str):
		if page == Section.BLANK:
			self.section = Section.BLANK
			self.subsection = 0
			self.document = 0
			self.page = 0
		elif match := GENERIC_PATTERN.match(page):
			self.section = Section(match.group(1))
			self.subsection = int(match.group(2))
			self.document = int(match.group(3))
			self.page = int(match.group(4))
		elif match := CHARTS_PATTERN.match(page):
			self.section = Section.AERODROME_CHARTS
			self.aerodrome = match.group(1)
			self.subsection = 0
			self.document = int(match.group(2))
			self.page = int(match.group(3))
			if match.group(4) == 'Y':
				self.flag = PageFlag.YELLOW
		else:
			raise ValueError(f"Invalid page format: {page}")
