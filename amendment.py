#GEN 0.4-401
import pathlib
import re
from enum import Enum
from typing import Optional

BLANK_PAGE = pathlib.Path(__file__).parent / "data" / "blank.pdf"

GENERIC_PATTERN = re.compile(r"([a-zA-Z]+) (\d+)\.(\d+)-(\d+)")
CHARTS_PATTERN = re.compile(r"(NZ[A-Z]{2}) AD 2-(\d+)\.(\d+)(Y?)")
