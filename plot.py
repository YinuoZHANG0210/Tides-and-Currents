# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pillow"]
# ///

"""Turn August 2026 NOAA water-level observations into a tidal-flow animation.

    uv run plot.py

The script reads only the committed JSON in data/, so it makes both outputs with
wifi off. Each GIF frame is one UTC day; every one of that day's 240 six-minute
observations becomes one curved, luminous filament.
"""

import json
import math
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # write files reliably, including on GitHub Actions
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle

FILE = "noaa-san-francisco-water-level-2026-08.json"
ANIMATION = "tidal-mycelium-2026-08.gif"
STILL = "tidal-mycelium-still.png"

HERE = Path(__file__).parent
DATA = HERE / "data" / FILE
OUT = HERE / "out"


def observations(path):
    """Read every NOAA observation, preserving its time, level, and QC fields."""
    with path.open(encoding="utf-8") as handle:
        reply = json.load(handle)

    records = []
    for row in reply["data"]:  # one loop over the raw NOAA measurements
        records.append(
            {
                "time": datetime.strptime(row["t"], "%Y-%m-%d %H:%M"),
                "level": float(row["v"]),
                "sigma": float(row["s"]),
                "flags": row["f"],
                "quality": row["q"],
            }
        )
    return records


def group_by_day(records):
    """Return the 31 UTC days, each containing 240 six-minute readings."""
    days = {}
    for record in records:
        days.setdefault(record["time"].date(), []).append(record)
    return list(days.values())


def mix(first, second, amount):
    """Blend two RGB colours using an amount between zero and one."""
    return tuple(a + (b - a) * amount for a, b in zip(first, second))


def colour(level_fraction, rising):
    """Low water is deep teal; high water is pale gold; rise adds cyan."""
    low = (0.04, 0.22, 0.30)
    high = (0.96, 0.79, 0.45)
    base = mix(low, high, level_fraction)
    return mix(base, (0.28, 0.90, 0.92), 0.25 if rising else 0.0)


def draw_day(ax, day, low_level, high_level, change_scale, smallest_range, largest_range):
    """Draw one day as 240 data-driven tidal filaments."""
    ax.clear()
    ax.set_facecolor("#06131c")
    ax.set_aspect("equal")
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.axis("off")

    day_range = max(row["level"] for row in day) - min(row["level"] for row in day)
    range_fraction = (day_range - smallest_range) / (largest_range - smallest_range)
    ax.add_patch(Circle((0, 0), 0.76 + 0.15 * range_fraction, color="#16616d", alpha=0.10))

    paths, colours, widths = [], [], []
    for slot, row in enumerate(day):
        # t fixes the root's place around the clock: 240 slots = 24 UTC hours.
        clock_angle = 2 * math.pi * slot / len(day) - math.pi / 2
        level_fraction = (row["level"] - low_level) / (high_level - low_level)
        previous = day[max(0, slot - 1)]["level"]
        change = row["level"] - previous
        change_fraction = max(-1.0, min(1.0, change / change_scale))

        # v controls radial position, reach, brightness, and stroke width.
        radius = 0.18 + 0.47 * level_fraction
        reach = 0.05 + 0.24 * level_fraction
        # The sign of Δv makes rising and falling tide curl in opposite directions.
        curl = 0.11 + 0.44 * change_fraction
        wiggle = 0.018 + 0.010 * math.sin(slot * 0.53)

        filament = []
        for step in range(9):
            progress = step / 8
            angle = clock_angle + curl * progress + wiggle * math.sin(progress * math.pi * 3)
            distance = radius + reach * progress + wiggle * math.sin(slot * 0.17 + step)
            filament.append((distance * math.cos(angle), distance * math.sin(angle)))
        paths.append(filament)

        has_flag = row["flags"] != "0,0,0,0"
        alpha = 0.18 if has_flag else (0.82 if row["quality"] == "v" else 0.36)
        red, green, blue = colour(level_fraction, change >= 0)
        colours.append((red, green, blue, alpha))
        widths.append(0.35 + 1.65 * level_fraction)

    ax.add_collection(LineCollection(paths, colors=colours, linewidths=widths, capstyle="round"))
    ax.text(0, 0.03, day[0]["time"].strftime("%d AUG"), color="#e8f7f7", ha="center",
            va="center", fontsize=17, weight="bold")
    ax.text(0, -0.06, "SAN FRANCISCO · UTC", color="#83a5ac", ha="center", va="center", fontsize=7)
    for hour in range(0, 24, 6):
        angle = 2 * math.pi * hour / 24 - math.pi / 2
        ax.text(1.02 * math.cos(angle), 1.02 * math.sin(angle), f"{hour:02d}",
                color="#54717a", ha="center", va="center", fontsize=8)


def canvas():
    """Make the dark square canvas shared by the GIF and its README still."""
    return plt.subplots(figsize=(7, 7), facecolor="#06131c")


def main():
    records = observations(DATA)
    days = group_by_day(records)
    levels = [row["level"] for row in records]
    changes = [records[index]["level"] - records[index - 1]["level"] for index in range(1, len(records))]
    low_level, high_level = min(levels), max(levels)
    change_scale = max(abs(change) for change in changes)
    daily_ranges = [max(row["level"] for row in day) - min(row["level"] for row in day) for day in days]
    smallest_range, largest_range = min(daily_ranges), max(daily_ranges)
    widest_day = days[daily_ranges.index(largest_range)]

    print(f"{DATA.name}: {len(records)} readings in {len(days)} UTC days.")
    print(f"Water level: {low_level:.3f} to {high_level:.3f} m above MLLW.")
    OUT.mkdir(exist_ok=True)

    fig, ax = canvas()
    animation_path = OUT / ANIMATION
    writer = PillowWriter(fps=4)
    with writer.saving(fig, animation_path, dpi=110):
        for day in days:
            draw_day(ax, day, low_level, high_level, change_scale, smallest_range, largest_range)
            ax.set_title(f"TIDAL MYCELIUM — {day[0]['time']:%d %b}", color="#d8edf0", fontsize=10, pad=16)
            writer.grab_frame()
    print(f"saved out/{ANIMATION}")

    draw_day(ax, widest_day, low_level, high_level, change_scale, smallest_range, largest_range)
    ax.set_title(f"TIDAL MYCELIUM — {widest_day[0]['time']:%d %b}", color="#d8edf0", fontsize=10, pad=16)
    fig.savefig(OUT / STILL, dpi=150, facecolor=fig.get_facecolor())
    print(f"saved out/{STILL}")
    plt.close(fig)


if __name__ == "__main__":
    main()
