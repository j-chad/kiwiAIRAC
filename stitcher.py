import uuid
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter

from aip_page import AIPPage, PageColour, Section, Sheet
from download import downloader, DownloadJob, RichProgressReporter

Url = str

async def stitch(sheets: Iterable[Sheet], output_dir: Path):
	"""Stitches the given sheets together into PDF files in the given output directory, grouped by colour."""
	if not output_dir.exists() or not output_dir.is_dir():
		raise ValueError(f"Output directory does not exist or is not a directory: {output_dir}")

	colour_groups = _group_by_colour(sheets)
	for colour, colour_sheets in colour_groups.items():
		file_name = "WHITE" if colour is None else colour.name
		file_path = output_dir / f"{file_name}.pdf"
		await _stitch_document(colour_sheets, file_path)

def _group_by_colour(sheets: Iterable[Sheet]) -> dict[PageColour | None, list[Sheet]]:
	"""Groups the given sheets by colour"""
	grouping: dict[PageColour | None, list[Sheet]] = {}

	for sheet in sheets:
		url = sheet.url
		if url is None:
			raise ValueError(f"Cannot group sheet with unknown URL: {sheet}")

		grouping.setdefault(sheet.colour, []).append(sheet)

	return grouping

async def _stitch_document(sheets: Iterable[Sheet], file_path: Path):
	"""Stitches the given sheets together into a single PDF file at the given file path."""
	writer = PdfWriter()

	runs = _find_url_runs(sheets)
	for run in runs:
		job = DownloadJob(run[0].url, content_types=["application/pdf"])
		with RichProgressReporter() as progress:
			document = await downloader.download(job, progress=progress)

		with open(document, "rb") as f:
			reader = PdfReader(f)
			for sheet in run:
				writer.add_page(reader.pages[sheet.front.page_number - 1])
				if sheet.is_duplex:
					writer.add_page(reader.pages[sheet.back.page_number - 1])


def _find_url_runs(sheets: Iterable[Sheet]) -> list[list[Sheet]]:
	"""Finds runs of sheets with the same URL, which minimises the number of IO operations when stitching the sheets together."""
	runs: list[list[Sheet]] = []
	current_run: list[Sheet] = []
	current_url: Url | None = None

	for sheet in sheets:
		url = sheet.url
		if url is None:
			raise ValueError(f"Cannot find URL for sheet: {sheet}")

		if url != current_url:
			if current_run:
				runs.append(current_run)
			current_run = [sheet]
			current_url = url
		else:
			current_run.append(sheet)

	if current_run:
		runs.append(current_run)

	return runs
