AERODROME_ICAO_MAP: dict[str, str] = {'NZLX': 'Alexandra', 'NZAN': 'Anama', 'NZAR': 'Ardmore', 'NZAS': 'Ashburton', 'NZAM': 'Ashburton Medical Centre', 'NZAA': 'Auckland', 'NZAW': 'Auckland Harbour', 'NZJL': 'Auckland Hospital', 'NZBA': 'Balclutha', 'NZJI': 'Bay Of Islands Hospital', 'NZBW': 'Burwood Hospital', 'NZCG': 'Centennial Park', 'NZCB': 'Centre Bush', 'NZCI': 'Chatham Is/Tuuta', 'NZCV': 'Cheviot', 'NZCH': 'Christchurch', 'NZJC': 'Christchurch Hospital', 'NZJJ': 'Christchurch Hospital Hagley', 'NZCL': 'Cloudy Bay', 'NZCS': 'Cromwell Racecourse', 'NZDV': 'Dannevirke', 'NZDA': 'Dargaville', 'NZJE': 'Dargaville Hospital', 'NZDY': 'Drury', 'NZDN': 'Dunedin', 'NZDC': 'Dunedin City', 'NZDH': 'Dunedin Hospital', 'NZDU': 'Dunstan Hospital', 'NZEV': 'Eves Valley', 'NZFI': 'Feilding', 'NZFG': 'Fern Gully', 'NZFE': 'Fernside Fields', 'NZFT': 'Flat Point', 'NZFF': 'Forest Field', 'NZFH': 'Fox', 'NZFO': 'Fox Glacier', 'NZFP': 'Foxpine', 'NZFR': 'Fox River', 'NZFJ': 'Franz Josef', 'NZGS': 'Gisborne', 'NZJG': 'Gisborne Hospital', 'NZGH': 'Glacier Country', 'NZGY': 'Glenorchy', 'NZGT': 'Glentanner', 'NZGC': 'Gore', 'NZGO': 'Gore Hospital', 'NZGB': 'Great Barrier', 'NZGM': 'Greymouth', 'NZHT': 'Haast', 'NZHN': 'Hamilton', 'NZHM': 'Hanmer', 'NZHR': 'Hanmer Medical Centre', 'NZHS': 'Hastings', 'NZJH': 'Hastings Hospital', 'NZHA': 'Hawera', 'NZHB': 'Helena Bay', 'NZHK': 'Hokitika', 'NZHF': 'Huka Falls', 'NZNV': 'Invercargill', 'NZKO': 'Kaikohe', 'NZKC': 'Kaikoura Medical Centre', 'NZKF': 'Kaipara Flats', 'NZKT': 'Kaitaia', 'NZJK': 'Kaitaia Hospital', 'NZKM': 'Karamea', 'NZWE': 'Kauaroa Bay', 'NZKH': 'Kenepuru Hospital', 'NZKN': 'Kensington Park', 'NZKK': 'Kerikeri/Bay Of Islands', 'NZKP': 'Koputaroa', 'NZKY': 'Kowhai', 'NZKU': 'Kupe', 'NZHP': 'Lake Haupiri', 'NZLE': 'Lake Station/Nelson Lakes', 'NZLA': 'Loburn Abbey', 'NZLM': 'Lumsden Medical Centre', 'NZMW': 'Makarora', 'NZOG': 'Makarora Heliport', 'NZVL': 'Mandeville', 'NZMG': 'Mangonui', 'NZSO': 'Marlborough Sounds', 'NZMA': 'Matamata', 'NZUA': 'Maui A', 'NZUB': 'Maui B', 'NZMB': 'Mechanics Bay', 'NZME': 'Mercer', 'NZMV': 'Methven', 'NZMM': 'Middlemore Hospital', 'NZML': 'Mid Waiho Loop', 'NZMF': 'Milford Sound', 'NZMK': 'Motueka', 'NZKD': 'Motu Kaikoura Island', 'NZMC': 'Mount Cook', 'NZMR': 'Murchison', 'NZUR': 'Murchison Hospital', 'NZNR': 'Napier', 'NZNS': 'Nelson', 'NZNH': 'Nelson Hospital', 'NZNP': 'New Plymouth', 'NZNF': 'Norfolk', 'NZNE': 'North Shore', 'NZJN': 'North Shore Hospital', 'NZON': 'Oban', 'NZOB': 'Ocean Beach', 'NZOH': 'Ohakea', 'NZOX': 'Okiwi Station', 'NZOF': 'Omaha Flats', 'NZOM': 'Omaka', 'NZOA': 'Omarama', 'NZOW': 'Onetangi', 'NZOI': 'Ongaio Island', 'NZOP': 'Opotiki', 'NZOT': 'Otaki', 'NZOS': 'Otehei Bay', 'NZPA': 'Paihia', 'NZPS': 'Paihia Waterfront', 'NZPM': 'Palmerston North', 'NZJM': 'Palmerston North Hospital', 'NZPW': 'Papawai', 'NZPI': 'Parakai', 'NZPN': 'Picton', 'NZPK': 'Pikes Point', 'NZPO': 'Porangahau', 'NZPH': 'Pudding Hill', 'NZUK': 'Pukaki', 'NZPU': 'Pukekohe', 'NZQN': 'Queenstown', 'NZQW': 'Queens Wharf', 'NZRA': 'Raglan', 'NZRI': 'Rakitata Island', 'NZRN': 'Ranfurly Medical Centre', 'NZRT': 'Rangiora', 'NZRK': 'Rangitaiki', 'NZMX': 'Raroa', 'NZJW': 'Rawene Hospital', 'NZRD': 'Rosedale', 'NZRO': 'Rotorua', 'NZJO': 'Rotorua Hospital', 'NZLF': 'Rotorua Lakefront', 'NZRL': 'Rotorua Lakes', 'NZRX': 'Roxburgh', 'NZRC': 'Ryans Creek', 'NZJS': 'Southland-Kew Hospital', 'NZSF': 'Springfield', 'NZSL': 'Springhill', 'NZSD': 'Stratford', 'NZAH': 'Taharoa Ironsands', 'NZTI': 'Taieri', 'NZVR': 'Taihape', 'NZTK': 'Takaka', 'NZTC': 'Tapanui Medical Centre', 'NZJQ': 'Taranaki Base Hospital', 'NZTS': 'Tasman', 'NZTM': 'Taumarunui', 'NZJT': 'Taumarunui Hospital', 'NZAP': 'Taupo', 'NZJZ': 'Taupo Hospital', 'NZLT': 'Taupo Water', 'NZTG': 'Tauranga', 'NZJA': 'Tauranga Hospital', 'NZTJ': 'Tawhaki', 'NZMO': 'Te Anau / Manapouri', 'NZFA': 'Te Hapua', 'NZTL': 'Tekapo', 'NZTP': 'Tekapo / Mackenzie', 'NZTE': 'Te Kowhai', 'NZTT': 'Te Kuiti', 'NZTQ': 'Te Kuiti Hospital', 'NZJP': 'Te Puia Springs Hospital', 'NZTH': 'Thames', 'NZJD': 'Thames Hospital', 'NZTU': 'Timaru', 'NZTZ': 'Timaru Hospital', 'NZTO': 'Tokoroa', 'NZJX': 'Tokoroa Hospital', 'NZTN': 'Turangi', 'NZTW': 'Twizel Medical Centre', 'NZKE': 'Waiheke', 'NZWV': 'Waihi Beach', 'NZHH': 'Waikato Hospital', 'NZWM': 'Waimate', 'NZYP': 'Waipukurau', 'NZMH': 'Wairarapa Hospital', 'NZJY': 'Wairoa Hospital', 'NZWQ': 'Waitiki', 'NZWF': 'Wanaka', 'NZHC': 'Wanaka Lakes Health Centre', 'NZWZ': 'Warkworth', 'NZWN': 'Wellington', 'NZWH': 'Wellington Hospital', 'NZWJ': 'Wellsford', 'NZWL': 'West Melton', 'NZWS': 'Westport', 'NZWK': 'Whakatane', 'NZJF': 'Whakatane Hospital', 'NZWG': 'Whangamata', 'NZWU': 'Whanganui', 'NZJU': 'Whanganui Hospital', 'NZWR': 'Whangarei', 'NZJR': 'Whangarei Hospital', 'NZES': 'Wharepapa South', 'NZWP': 'Whenuapai'}


async def _main():
	"""
	Quick and dirty script to extract aerodrome ICAO mappings from the AIP aerodrome coordinates PDF.
	"""
	import camelot

	from download import RichProgressReporter, downloader, DownloadJob

	aerodrome_table_job = DownloadJob(
		url='https://www.aip.net.nz/assets/AIP/Air-Navigation-Register/5-Aerodromes/NZANR-Aerodrome_Coordinates.pdf',
		content_types=['application/pdf'])
	with RichProgressReporter() as progress:
		aerodrome_path = await downloader.download(aerodrome_table_job, progress=progress)

	aerodromes: dict[str, str] = {}

	tables = camelot.read_pdf(str(aerodrome_path), pages='all', parallel=True)
	for table in tables:
		# skip the first 2 rows which are just headers
		for _, row in table.df.iloc[2:].iterrows():
			name = row[0].strip()
			icao = row[2].strip()
			if not icao or not name:
				raise ValueError(f"Invalid row in aerodrome table: {row}")
			if not icao.startswith('NZ'):
				raise ValueError(f"Invalid ICAO code in aerodrome table: {icao}")

			# title case the name
			name = name.title()

			aerodromes[icao] = name

	print(aerodromes)


if __name__ == '__main__':
	import asyncio

	raise SystemExit(asyncio.run(_main()))
