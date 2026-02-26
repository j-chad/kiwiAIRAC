import enum
from typing import Optional

import requests
import bs4

URL = "https://www.aip.net.nz/"
HEADER = "Additional documents"

class DocumentType(enum.Enum):
	Supplement = "AIP Supplement"
	StandaloneSupplement = "AIP Supplement - Standalone"
	AeronauticalInformationCircular = "Aeronautical Information Circular"
	ChangesBulletin = "Changes Bulletin"
	Unknown = "Unknown"

class AdditionalDocument:
	type: DocumentType
	title: str
	url: str
	effective_date: Optional[str]

	def __init__(self, doc_type: DocumentType, title: str, url: str):
		self.type = doc_type
		self.title = title
		self.url = url

def load_additional_documents() -> list[AdditionalDocument]:
	"""fetches the list of additional documents from the AIP website"""
	response = requests.get(URL)
	response.raise_for_status()

	soup = bs4.BeautifulSoup(response.text, "html.parser")

	# find the div with the text "Additional documents"
	header_div = soup.find("div", text=HEADER)
	if header_div is None:
		raise ValueError(f"Could not find header '{HEADER}' on the page")

if __name__ == "__main__":
	docs = load_additional_documents()
	for doc in docs:
		print(f"{doc.type.value}: {doc.title} ({doc.url})")
