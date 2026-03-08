from datetime import date
from pathlib import Path

from checklist import Checklist
from models import Subscription
from stitcher import stitch


async def main():
	checklist = await Checklist.fetch()
	checklist.volumes(Subscription.VISUAL).effective_after(date(2026, 2, 17))
	checklist.sheets()

	sheets = checklist.sheets()

	await stitch(sheets, Path("output"))


	# update_pdf = stitch_duplex(checklist)
	# change_pdf = generate_change_pdf(checklist)

if __name__ == "__main__":
	import asyncio
	raise SystemExit(asyncio.run(main()))
