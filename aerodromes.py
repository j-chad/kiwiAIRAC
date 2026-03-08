import json
from pathlib import Path

# Table can be updated by running the following code in the browser console on the charts page:
# https://www.aip.net.nz/document-category/Aerodrome-Charts/
# console.log(JSON.stringify([...document.querySelectorAll('a.file-info__link')].reduce((a,i)=>(m=/Aerodrome-Charts\/([A-Za-z0-9_-]+-(NZ[A-Z]{2})\/\2(_\d+\.\d+[YG]?)*)\.pdf/.exec(i.href),(a[m[2]]??=[]).push(m[1]),a),{})))
AERODROME_CHART_DATA_FILE = Path(__file__).parent / "data" / "aerodrome_chart_files.json"

with AERODROME_CHART_DATA_FILE.open("r") as f:
	AERODROME_CHART_DATA: dict[str, list[str]] = json.load(f)
