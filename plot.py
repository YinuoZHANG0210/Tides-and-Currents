# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pillow"]
# ///

"""Render NOAA water levels as a growing, dissolving tidal-flow field.

    uv run plot.py

The renderer reads only the committed JSON in data/. Each of the 7,440 NOAA
observations becomes a long streamline in a custom two-dimensional flow field.
Eight frames reveal each UTC day in sequence, so the GIF follows the
measurements' real order without fetching anything.
"""

import json
import math
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # create image files reliably, including on GitHub Actions
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter
from matplotlib.collections import LineCollection

FILE = "noaa-san-francisco-water-level-2026-08.json"
ANIMATION = "tidal-mycelium-2026-08.gif"
STILL = "tidal-mycelium-still.png"
STEPS_PER_DAY = 8  # one animated step per three hours of observations

HERE = Path(__file__).parent
DATA = HERE / "data" / FILE
OUT = HERE / "out"


def observations(path):
    """Read every NOAA observation and retain the original measurement fields."""
    with path.open(encoding="utf-8") as handle:
        reply = json.load(handle)

    records = []
    for row in reply["data"]:  # loop over all 7,440 raw NOAA records
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
    """Group the six-minute observations into 31 UTC days of 240 records."""
    days = {}
    for record in records:
        days.setdefault(record["time"].date(), []).append(record)
    return list(days.values())


def clamp(value, lower=0.0, upper=1.0):
    """Keep a visual parameter within its usable range."""
    return max(lower, min(upper, value))


def mix(first, second, amount):
    """Blend two RGB colours using an amount between zero and one."""
    return tuple(a + (b - a) * amount for a, b in zip(first, second))


def colour(level_fraction, rising):
    """Map low water to teal and high water to luminous mineral gold."""
    low = (0.03, 0.25, 0.33)
    high = (0.96, 0.72, 0.31)
    base = mix(low, high, level_fraction)
    return mix(base, (0.24, 0.91, 0.92), 0.30 if rising else 0.0)


def day_stats(day, low_level, high_level, smallest_range, largest_range):
    """Derive the day's mean and tidal range from its 240 actual readings."""
    levels = [row["level"] for row in day]
    day_mean = sum(levels) / len(levels)
    day_range = max(levels) - min(levels)
    mean_fraction = (day_mean - low_level) / (high_level - low_level)
    range_fraction = (day_range - smallest_range) / (largest_range - smallest_range)
    return mean_fraction, range_fraction, day_mean, day_range


def filament_collections(day, flow_phase, parameters, change_scale):
    """Make a complete, slowly moving field from one day's 240 observations."""
    mean_fraction, range_fraction = parameters[:2]
    spread = 0.46 + 0.82 * range_fraction ** 0.72
    core = 0.13 + 0.25 * (1 - range_fraction) + 0.06 * (1 - mean_fraction)
    paths, colours, glow_colours, widths = [], [], [], []

    for slot, row in enumerate(day):
        time_fraction = slot / (len(day) - 1)
        # A soft, slow highlight travels round the clock. All 240 records remain
        # present in every frame, rather than forming a first/second-stage image.
        freshness = max(0, math.cos(2 * math.pi * (time_fraction - flow_phase))) ** 10
        level_fraction = clamp((row["level"] - parameters[4]) / (parameters[5] - parameters[4]))
        previous = day[max(0, slot - 1)]["level"]
        change_fraction = clamp((row["level"] - previous) / change_scale, -1.0, 1.0)

        # The observation's clock time defines its source position in the flow field.
        base_angle = 2 * math.pi * time_fraction - math.pi / 2 + 0.70 * (mean_fraction - 0.5)
        radius = core + (0.14 + 0.42 * level_fraction) * spread
        # Long reach and a signed sweep create a water-current-like trail. They
        # remain determined by v and its six-minute change, not random particles.
        reach = (0.13 + 0.52 * level_fraction) * spread
        curl = 0.16 + 0.86 * change_fraction
        sweep = (0.28 + 0.36 * level_fraction + 0.42 * abs(change_fraction))
        sweep *= 1 if change_fraction >= 0 else -1
        drift = 0.08 * math.sin(2 * math.pi * (flow_phase - time_fraction))
        wiggle = 0.022 + 0.035 * range_fraction

        thread = []
        for step in range(42):
            progress = step / 41
            wave = math.sin(slot * 0.19 + step * 0.64 + flow_phase * math.pi * 2)
            eddy = math.sin(slot * 0.07 - step * 0.31 + flow_phase * math.pi)
            angle = base_angle + (curl + drift) * progress + sweep * progress ** 1.28 + wiggle * wave
            distance = radius + reach * progress + wiggle * 1.8 * eddy * (1 - progress * 0.35)
            thread.append((distance * math.cos(angle), distance * math.sin(angle)))
        paths.append(thread)

        flagged = row["flags"] != "0,0,0,0"
        quality_alpha = 0.76 if row["quality"] == "v" else 0.30
        alpha = quality_alpha * (0.62 + 0.38 * freshness) * (0.18 if flagged else 1.0)
        red, green, blue = colour(level_fraction, change_fraction >= 0)
        red, green, blue = mix((red, green, blue), (0.92, 0.99, 0.96), 0.08 + 0.42 * freshness)
        colours.append((red, green, blue, alpha))
        glow_colours.append((red, green, blue, alpha * 0.11))
        widths.append((0.16 + 0.82 * level_fraction) * (0.72 + 0.48 * range_fraction))

    glow = LineCollection(paths, colors=glow_colours, linewidths=[width + 1.8 for width in widths], capstyle="round")
    threads = LineCollection(paths, colors=colours, linewidths=widths, capstyle="round")
    return glow, threads


def water_ripples(ax, parameters, flow_phase):
    """Draw broad, data-driven water ripples behind the streamlines."""
    mean_fraction, range_fraction = parameters[:2]
    paths, colours, widths = [], [], []
    for ring in range(7):
        points = []
        base_radius = 0.34 + ring * 0.14 + 0.24 * range_fraction
        amplitude = 0.010 + (0.014 + 0.020 * range_fraction) * (ring + 1) / 7
        for step in range(121):
            angle = 2 * math.pi * step / 120
            wave = math.sin((2 + ring % 3) * angle - flow_phase * math.pi * 2)
            cross_wave = 0.45 * math.sin((5 + ring) * angle + mean_fraction * math.pi * 2)
            radius = base_radius + amplitude * (wave + cross_wave)
            points.append((radius * math.cos(angle), radius * math.sin(angle)))
        paths.append(points)
        colours.append((0.08, 0.46, 0.57, 0.07 + 0.025 * range_fraction))
        widths.append(0.30 + 0.15 * ring)
    ax.add_collection(LineCollection(paths, colors=colours, linewidths=widths))


def draw_frame(ax, day, flow_phase, parameters, change_scale):
    """Draw one complete daily field with a gently moving water surface."""
    mean_fraction, range_fraction, day_mean, day_range, low_level, high_level = parameters
    ax.clear()
    ax.set_facecolor("#040b12")
    ax.set_aspect("equal")
    ax.set_xlim(-1.62, 1.62)
    ax.set_ylim(-1.62, 1.62)
    ax.axis("off")

    water_ripples(ax, parameters, flow_phase)
    glow, threads = filament_collections(day, flow_phase, parameters, change_scale)
    ax.add_collection(glow)
    ax.add_collection(threads)

    date_label = day[0]["time"].strftime("%d AUG 2026")
    ax.text(-1.46, 1.42, "TIDE / FIELD", color="#70aab4", fontsize=8, weight="bold", ha="left")
    ax.text(-1.46, 1.29, date_label, color="#e6f4ed", fontsize=15, weight="bold", ha="left")
    ax.text(-1.46, -1.43, f"MEAN {day_mean:0.2f} M", color="#78949b", fontsize=8, ha="left")
    ax.text(1.46, -1.43, f"RANGE {day_range:0.2f} M", color="#e3be70", fontsize=8, ha="right")
    ax.text(0, 0.09, "00 — 24", color="#f1f6ec", fontsize=18, ha="center", va="center")
    ax.text(0, -0.16, "UTC · SAN FRANCISCO", color="#7d9aa0", fontsize=7, ha="center", va="center")


def canvas():
    """Make the square canvas shared by the GIF and its README still image."""
    return plt.subplots(figsize=(6, 6), facecolor="#040b12")


def main():
    records = observations(DATA)
    days = group_by_day(records)
    levels = [row["level"] for row in records]
    changes = [records[index]["level"] - records[index - 1]["level"] for index in range(1, len(records))]
    low_level, high_level = min(levels), max(levels)
    change_scale = max(abs(change) for change in changes)
    daily_ranges = [max(row["level"] for row in day) - min(row["level"] for row in day) for day in days]
    smallest_range, largest_range = min(daily_ranges), max(daily_ranges)
    parameters = [
        (*day_stats(day, low_level, high_level, smallest_range, largest_range), low_level, high_level)
        for day in days
    ]
    widest_index = daily_ranges.index(largest_range)

    print(f"{DATA.name}: {len(records)} readings in {len(days)} UTC days.")
    print(f"Water level: {low_level:.3f} to {high_level:.3f} m above MLLW.")
    OUT.mkdir(exist_ok=True)

    fig, ax = canvas()
    writer = PillowWriter(fps=8)
    with writer.saving(fig, OUT / ANIMATION, dpi=100):
        for index, day in enumerate(days):
            for step in range(STEPS_PER_DAY):
                flow_phase = step / STEPS_PER_DAY
                draw_frame(ax, day, flow_phase, parameters[index], change_scale)
                writer.grab_frame()
    print(f"saved out/{ANIMATION}")

    draw_frame(ax, days[widest_index], 0.0, parameters[widest_index], change_scale)
    fig.savefig(OUT / STILL, dpi=160, facecolor=fig.get_facecolor())
    print(f"saved out/{STILL}")
    plt.close(fig)


if __name__ == "__main__":
    main()
