# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///

"""Make a tide-level picture from the committed NOAA JSON file.

    uv run plot.py

The script reads data/ only, so it works without wifi. NOAA recorded one water
level every six minutes at San Francisco during August 2026.
"""

import json
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save a PNG; do not require a graphical desktop
import matplotlib.pyplot as plt

FILE = "noaa-san-francisco-water-level-2026-08.json"
PICTURE = "san-francisco-tides-2026-08.png"

HERE = Path(__file__).parent
DATA = HERE / "data" / FILE
OUT = HERE / "out"


def observations(path):
    """Return UTC datetimes and verified water levels in metres from NOAA JSON."""
    with path.open(encoding="utf-8") as handle:
        reply = json.load(handle)

    times, levels = [], []
    for row in reply["data"]:  # one loop over the measurements
        if row["q"] != "v":
            continue
        times.append(datetime.strptime(row["t"], "%Y-%m-%d %H:%M"))
        levels.append(float(row["v"]))
    return times, levels


def main():
    times, levels = observations(DATA)
    print(f"{DATA.name}: {len(levels)} verified measurements.")
    print(f"From {times[0]} to {times[-1]} UTC; {min(levels):.3f}–{max(levels):.3f} m.")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(times, levels, color="#176b87", linewidth=0.8)
    ax.fill_between(times, levels, 0, color="#9acbd7", alpha=0.35)
    ax.axhline(0, color="#475569", linewidth=0.8)
    ax.set_xlabel("date and time (UTC)")
    ax.set_ylabel("observed water level (m above MLLW)")
    ax.set_title("Tidal water level at San Francisco — August 2026")
    ax.grid(axis="y", color="#cbd5e1", linewidth=0.6)
    fig.tight_layout()

    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / PICTURE, dpi=150)
    print(f"saved out/{PICTURE}")


if __name__ == "__main__":
    main()
