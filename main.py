from datetime import date

from checklist import Checklist
from models import Subscription


async def main():
	checklist = await Checklist.fetch()
	checklist.volumes(Subscription.VISUAL).effective_after(date(2026, 2, 17))
	checklist.for_duplex_printing()


	update_pdf = stitch_duplex(checklist)
	change_pdf = generate_change_pdf(checklist)

if __name__ == "__main__":
	import asyncio
	raise SystemExit(asyncio.run(main()))
