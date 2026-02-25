import pathlib

import requests
import camelot
import tempfile

from camelot.core import Table

from amendments import Volume

CHECKLIST_URL = 'https://www.aip.net.nz/assets/AIP/General-GEN/0-GEN/GEN_0.4.pdf'

class ParseError(Exception):
	pass

def get_checklist_pdf() -> pathlib.Path:
	response = requests.get(CHECKLIST_URL)
	response.raise_for_status()

	with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
		f.write(response.content)
		return pathlib.Path(f.name)

def get_checklist_pages_for_volume(pdf_path: pathlib.Path, volume: Volume) -> list[int]:
	

def parse_checklist(pdf_path: pathlib.Path):
	tables = camelot.read_pdf(pdf_path, pages='all', flavor='network', parallel=True)
	if tables.n == 0:
		raise ParseError("No tables found in the PDF")
	if tables.n > 1:
		raise ParseError("Multiple tables found in the PDF")

	table: Table = tables[0]
	if table.parsing_report['accuracy'] < 90:
		raise ParseError(f"Low parsing accuracy: {table.parsing_report['accuracy']}%")



if __name__ == '__main__':
	pdf_path = pathlib.Path('/Users/jackson.chadfield/code/personal/kiwiAIRAC/test/GEN_0.4.pdf')
	outdated_files = parse_checklist(pdf_path)
	print("Outdated files:")
	for filename in outdated_files:
		print(filename)
