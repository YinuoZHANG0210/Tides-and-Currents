# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""
Fetch the numbers once, save the raw reply to data/, and never fetch again.

    uv run fetch.py

Download NOAA's six-minute observed water levels at San Francisco, California,
for August 2026. The first run saves NOAA's JSON response unchanged; later
runs use that committed file and do not make a network request.
"""

from pathlib import Path

import requests

URL = (
    "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    "?begin_date=20260801&end_date=20260831"
    "&station=9414290&product=water_level&datum=MLLW"
    "&time_zone=gmt&units=metric"
    "&application=TidesAndCurrentsAssignment&format=json"
)
FILE = "noaa-san-francisco-water-level-2026-08.json"
HERE = Path(__file__).parent
DATA = HERE / "data"


def fetch(url, path):
    """Ask for the file once. If it is already in data/, do nothing."""
    if path.exists():
        print(f"data/{path.name} is already here ({path.stat().st_size // 1024} KB). "
              "Delete it to fetch again.")
        return path
    DATA.mkdir(exist_ok=True)
    print(f"asking {url}")
    reply = requests.get(url, timeout=60, headers={"User-Agent": "SD5913 PolyU student"})
    reply.raise_for_status()
    path.write_bytes(reply.content)      # the raw reply, byte for byte: what arrived is what gets committed
    print(f"saved data/{path.name} ({path.stat().st_size // 1024} KB). Now: git add data")
    return path


if __name__ == "__main__":
    fetch(URL, DATA / FILE)
