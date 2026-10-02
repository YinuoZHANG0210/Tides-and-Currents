# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""
Fetch the numbers once, save the raw reply to data/, and never fetch again.

    uv run fetch.py

Download NOAA's six-minute observed water levels at San Francisco, California,
from October 2025 through September 2026. NOAA limits an observed-water-level
request to 31 days, so this script saves one unchanged raw JSON reply per
calendar month. Later runs use the committed files and do not make a network
request.
"""

from datetime import date
from pathlib import Path
import time

import requests

HERE = Path(__file__).parent
DATA = HERE / "data"
MONTHS = [(2025, month) for month in range(10, 13)] + [(2026, month) for month in range(1, 10)]


def following_month(year, month):
    """Return the first day of the calendar month after year-month."""
    return date(year + (month == 12), 1 if month == 12 else month + 1, 1)


def request_for_month(year, month):
    """Build one NOAA request and its stable local raw-file name."""
    start = date(year, month, 1)
    end = following_month(year, month) - start.resolution
    url = (
        "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        f"?begin_date={start:%Y%m%d}&end_date={end:%Y%m%d}"
        "&station=9414290&product=water_level&datum=MLLW"
        "&time_zone=gmt&units=metric"
        "&application=TidesAndCurrentsAssignment&format=json"
    )
    return url, DATA / f"noaa-san-francisco-water-level-{year}-{month:02}.json"


def fetch(url, path):
    """Ask for the file once. If it is already in data/, do nothing."""
    if path.exists():
        print(f"data/{path.name} is already here ({path.stat().st_size // 1024} KB). "
              "Delete it to fetch again.")
        return path
    DATA.mkdir(exist_ok=True)
    print(f"asking NOAA for {path.stem[-7:]}")
    reply = requests.get(url, timeout=60, headers={"User-Agent": "SD5913 PolyU student"})
    reply.raise_for_status()
    path.write_bytes(reply.content)      # the raw reply, byte for byte: what arrived is what gets committed
    print(f"saved data/{path.name} ({path.stat().st_size // 1024} KB). Now: git add data")
    return path


if __name__ == "__main__":
    for index, (year, month) in enumerate(MONTHS):
        url, path = request_for_month(year, month)
        existed = path.exists()
        fetch(url, path)
        # Be gentle when this is a first run with several missing months.
        if not existed and index < len(MONTHS) - 1:
            time.sleep(0.5)
