# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pillow"]
# ///

"""Render twelve cached NOAA months as a 3 × 4 field of tidal-flow rings.

    uv run plot.py

Each small ring keeps the animated visual language of the original August
version. All twelve rings loop through their own month in parallel, from the
first UTC day to the last; their accents shift gradually through the year.
"""

import colorsys
import json
import math
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter
from matplotlib.collections import LineCollection

WINDOW = [(2025, month) for month in range(10, 13)] + [(2026, month) for month in range(1, 10)]
MONTH_NAMES = ("OCT", "NOV", "DEC", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP")
ANIMATION = "tide-traces-year-2025-10-to-2026-09.gif"
STILL = "tide-traces-year-still.png"
FRAMES_PER_LOOP = 144
HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out"


def monthly_file(year, month):
    """Return the committed raw JSON file for one NOAA calendar month."""
    return DATA / f"noaa-san-francisco-water-level-{year}-{month:02}.json"


def observations(path):
    """Read every NOAA observation and retain all five measurement fields."""
    with path.open(encoding="utf-8") as handle:
        reply = json.load(handle)
    records = []
    for row in reply["data"]:
        records.append(
            {
                "time": datetime.strptime(row["t"], "%Y-%m-%d %H:%M"),
                "level": float(row["v"]),
                "sigma": float(row["s"]) if row["s"] else None,
                "flags": row["f"],
                "quality": row["q"],
            }
        )
    return records


def group_by_day(records):
    """Group chronological six-minute observations into UTC days."""
    grouped = {}
    for record in records:
        grouped.setdefault(record["time"].date(), []).append(record)
    return list(grouped.values())


def clamp(value, lower=0.0, upper=1.0):
    """Keep a visual fraction inside a usable range."""
    return max(lower, min(upper, value))


def mix(first, second, amount):
    """Blend two RGB triples."""
    return tuple(a + (b - a) * amount for a, b in zip(first, second))


def smooth(value):
    """Ease a new trace into view rather than giving it a hard edge."""
    value = clamp(value)
    return value * value * (3 - 2 * value)


def month_profiles(months):
    """Measure the differences that give every monthly field its own character."""
    raw = []
    for days in months:
        values = [row["level"] for day in days for row in day]
        daily_ranges = [max(row["level"] for row in day) - min(row["level"] for row in day) for day in days]
        raw.append((sum(values) / len(values), max(values) - min(values), sum(daily_ranges) / len(daily_ranges)))
    means, spans, daily_ranges = zip(*raw)
    profiles = []
    for mean, span, daily_range in raw:
        mean_fraction = (mean - min(means)) / (max(means) - min(means))
        span_fraction = (span - min(spans)) / (max(spans) - min(spans))
        daily_range_fraction = (daily_range - min(daily_ranges)) / (max(daily_ranges) - min(daily_ranges))
        energy = 0.58 * span_fraction + 0.42 * daily_range_fraction
        profiles.append(
            {
                "mean": mean,
                "span": span,
                "daily_range": daily_range,
                "mean_fraction": mean_fraction,
                "energy": energy,
                "field_scale": 0.72 + 0.58 * energy,
                "colour_signal": 0.65 * mean_fraction + 0.35 * energy,
            }
        )
    # Spread the twelve hues over the full palette by the rank of the measured
    # signal, rather than letting similar adjacent values collapse to one green.
    for rank, index in enumerate(sorted(range(len(profiles)), key=lambda item: profiles[item]["colour_signal"])):
        profiles[index]["colour_rank"] = rank / (len(profiles) - 1)
    return profiles


def month_accent(profile):
    """Colour a month from its measured mean height and tidal energy."""
    hue = 0.56 - 0.56 * profile["colour_rank"]
    saturation = 0.58 + 0.32 * profile["energy"]
    brightness = 0.70 + 0.25 * profile["mean_fraction"]
    return colorsys.hsv_to_rgb(hue, saturation, brightness)


def colour(level_fraction, rising, profile, freshness):
    """Keep each month's data-derived hue visibly present in every line."""
    accent = month_accent(profile)
    # v changes dark-to-light within one monthly hue instead of forcing every
    # high-water line toward the same gold. This keeps the 12 fields distinct.
    low = mix((0.01, 0.04, 0.08), accent, 0.42)
    high = mix(accent, (1.0, 1.0, 1.0), 0.22)
    base = mix(low, high, level_fraction)
    if rising:
        base = mix(base, mix(accent, (1.0, 0.93, 0.78), 0.38), 0.12)
    return mix(base, (1.0, 1.0, 1.0), 0.03 + 0.16 * freshness)


def day_stats(day, low_level, high_level, smallest_range, largest_range, sigma_low, sigma_high):
    """Derive one day's field spread and water ripple parameters."""
    levels = [row["level"] for row in day]
    sigmas = [row["sigma"] for row in day if row["sigma"] is not None]
    mean = sum(levels) / len(levels)
    return (
        (mean - low_level) / (high_level - low_level),
        (max(levels) - min(levels) - smallest_range) / (largest_range - smallest_range),
        mean,
        max(levels) - min(levels),
        sum(sigmas) / len(sigmas) if sigmas else sigma_low,
        low_level,
        high_level,
        sigma_low,
        sigma_high,
    )


def filament_collections(day, release, parameters, change_scale, profile, day_offset=0, stride=2):
    """Build fading, data-derived threads for one day in one monthly cell."""
    mean_fraction, range_fraction = parameters[:2]
    spread = (0.46 + 0.82 * range_fraction ** 0.72) * profile["field_scale"]
    core = 0.13 + 0.25 * (1 - range_fraction) + 0.06 * (1 - mean_fraction)
    paths, colours, glows, widths, glow_widths = [], [], [], [], []
    particle_paths, particle_colours, particle_widths = [], [], []

    for slot in range(0, len(day), stride):
        row = day[slot]
        time_fraction = slot / (len(day) - 1)
        age = day_offset + release - time_fraction
        if age < -0.002 or age >= 2.0:
            continue
        arrival = smooth((release - time_fraction + 0.018) * 24 * 1.5) if day_offset == 0 else 1.0
        persistence = (1 - clamp(age / 2.0)) ** 2.60
        freshness = math.exp(-2.40 * max(age, 0))
        level_fraction = clamp((row["level"] - parameters[5]) / (parameters[6] - parameters[5]))
        sigma_fraction = clamp(((row["sigma"] if row["sigma"] is not None else parameters[7]) - parameters[7]) / (parameters[8] - parameters[7]))
        previous = day[max(0, slot - 1)]["level"]
        change_fraction = clamp((row["level"] - previous) / change_scale, -1.0, 1.0)

        base_angle = math.tau * time_fraction - math.pi / 2 + 0.70 * (mean_fraction - 0.5)
        radius = core + (0.14 + 0.42 * level_fraction) * spread
        reach = (0.24 + 0.86 * level_fraction) * spread * (0.25 + 0.75 * arrival) * profile["field_scale"]
        curl = 0.16 + 0.86 * change_fraction
        sweep = (0.34 + 0.44 * level_fraction + 0.52 * abs(change_fraction))
        sweep *= 1 if change_fraction >= 0 else -1
        drift = 0.08 * math.sin(math.tau * (release - time_fraction))
        wiggle = (0.028 + 0.048 * range_fraction) * (0.78 + 0.34 * profile["energy"])

        thread = []
        for step in range(38):
            progress = step / 37
            wave = math.sin(slot * 0.19 + step * 0.64 + release * math.tau)
            eddy = math.sin(slot * 0.07 - step * 0.31 + release * math.pi)
            angle = base_angle + (curl + drift) * progress + sweep * progress ** 1.28 + wiggle * wave
            distance = radius + reach * progress + wiggle * 1.8 * eddy * (1 - progress * 0.35)
            thread.append((distance * math.cos(angle), distance * math.sin(angle)))

        alpha = (0.76 if row["quality"] == "v" else 0.30) * persistence * arrival * (0.62 + 0.38 * freshness)
        alpha *= 0.18 if row["flags"] != "0,0,0,0" else 1.0
        alpha = min(1.0, alpha * 1.34)
        red, green, blue = colour(level_fraction, change_fraction >= 0, profile, freshness)
        width = (0.15 + 0.68 * level_fraction) * (0.78 + 0.54 * range_fraction)
        paths.append(thread)
        colours.append((red, green, blue, alpha))
        glows.append((red, green, blue, alpha * (0.14 + 0.30 * sigma_fraction)))
        widths.append(width)
        glow_widths.append(width + 1.25 + 1.20 * sigma_fraction)
        particle_index = int(((release * 1.6 + time_fraction * 0.35) % 1) * (len(thread) - 2))
        particle_paths.append(thread[particle_index:particle_index + 2])
        particle_colours.append((0.96, 1.0, 0.98, alpha * (0.35 + 0.65 * freshness)))
        particle_widths.append(width + 1.00)

    return (
        LineCollection(paths, colors=glows, linewidths=glow_widths, capstyle="round"),
        LineCollection(paths, colors=colours, linewidths=widths, capstyle="round"),
        LineCollection(particle_paths, colors=particle_colours, linewidths=particle_widths, capstyle="round"),
    )


def water_ripples(ax, parameters, release, profile):
    """Draw a restrained, colour-shifting ripple field behind each month."""
    mean_fraction, range_fraction = parameters[:2]
    accent = month_accent(profile)
    paths, colours, widths = [], [], []
    for ring in range(6):
        points = []
        base_radius = (0.34 + ring * 0.15 + 0.24 * range_fraction) * profile["field_scale"]
        amplitude = (0.010 + (0.014 + 0.020 * range_fraction) * (ring + 1) / 6) * (0.72 + 0.60 * profile["energy"])
        for step in range(97):
            angle = math.tau * step / 96
            wave = math.sin((2 + ring % 3) * angle - release * math.tau)
            cross_wave = 0.45 * math.sin((5 + ring) * angle + mean_fraction * math.tau)
            radius = base_radius + amplitude * (wave + cross_wave)
            points.append((radius * math.cos(angle), radius * math.sin(angle)))
        paths.append(points)
        colours.append((*accent, 0.045 + 0.030 * range_fraction))
        widths.append(0.22 + 0.12 * ring)
    ax.add_collection(LineCollection(paths, colors=colours, linewidths=widths))


def draw_cell(ax, days, index, release, parameters, change_scale, month_index, profile):
    """Draw one month at its current fraction from month-start to month-end."""
    day = days[index]
    stats = parameters[index]
    ax.clear()
    ax.set_facecolor("#040b12")
    ax.set_aspect("equal")
    ax.set_xlim(-1.84, 1.84)
    ax.set_ylim(-1.84, 1.84)
    ax.axis("off")
    water_ripples(ax, stats, release, profile)
    for day_offset in (2, 1):
        source_index = index - day_offset
        if source_index >= 0:
            for collection in filament_collections(days[source_index], release, parameters[source_index], change_scale, profile, day_offset):
                ax.add_collection(collection)
    for collection in filament_collections(day, release, stats, change_scale, profile):
        ax.add_collection(collection)

    accent = month_accent(profile)
    day_label = day[0]["time"].strftime("%d %b %Y").upper()
    hour = min(24, round(release * 24))
    ax.text(-1.52, 1.42, MONTH_NAMES[month_index], color=accent, fontsize=8.0, weight="bold", ha="left")
    ax.text(-1.52, 1.27, day_label, color="#a6c0c2", fontsize=4.8, ha="left")
    ax.text(0, 0.07, f"{hour:02}:00", color="#eaf6ee", fontsize=9.0, weight="bold", ha="center")
    ax.text(0, -0.10, "UTC", color=accent, fontsize=4.4, weight="bold", ha="center")


def draw_grid(axes, months, profiles, progress, parameters, change_scale):
    """Advance every monthly cell through the same normalized annual loop."""
    for month_index, days in enumerate(months):
        position = progress * len(days)
        index = min(int(position), len(days) - 1)
        release = position - int(position)
        draw_cell(axes.flat[month_index], days, index, release, parameters[month_index], change_scale, month_index, profiles[month_index])


def main():
    """Load the year once, then render a looping GIF and a matching still."""
    raw_months = [observations(monthly_file(year, month)) for year, month in WINDOW]
    months = [group_by_day(records) for records in raw_months]
    profiles = month_profiles(months)
    all_records = [record for records in raw_months for record in records]
    all_days = [day for month in months for day in month]
    levels = [record["level"] for record in all_records]
    sigmas = [record["sigma"] for record in all_records if record["sigma"] is not None]
    daily_ranges = [max(row["level"] for row in day) - min(row["level"] for row in day) for day in all_days]
    changes = [all_records[index]["level"] - all_records[index - 1]["level"] for index in range(1, len(all_records))]
    low_level, high_level = min(levels), max(levels)
    parameters = [
        [day_stats(day, low_level, high_level, min(daily_ranges), max(daily_ranges), min(sigmas), max(sigmas)) for day in month]
        for month in months
    ]
    change_scale = max(abs(change) for change in changes)

    print(f"{len(all_records):,} readings in 12 cached months / {len(all_days)} UTC days.")
    print(f"Water level: {low_level:.3f} to {high_level:.3f} m above MLLW.")
    for name, profile in zip(MONTH_NAMES, profiles):
        print(f"{name}: mean {profile['mean']:.3f} m, span {profile['span']:.3f} m, daily range {profile['daily_range']:.3f} m")
    OUT.mkdir(exist_ok=True)
    figure, axes = plt.subplots(3, 4, figsize=(16, 12), facecolor="#040b12")
    figure.subplots_adjust(left=0.018, right=0.982, top=0.94, bottom=0.018, wspace=0, hspace=0)
    figure.text(0.03, 0.972, "TIDE TRACES", color="#e4f3ed", fontsize=15, weight="bold")
    figure.text(0.18, 0.973, "SAN FRANCISCO · 01 OCT 2025 — 30 SEP 2026 · NOAA 9414290", color="#76a0a8", fontsize=6.8)

    writer = PillowWriter(fps=3)  # 48 seconds per complete twelve-month loop
    with writer.saving(figure, OUT / ANIMATION, dpi=78):
        for frame in range(FRAMES_PER_LOOP):
            draw_grid(axes, months, profiles, (frame + 1) / FRAMES_PER_LOOP, parameters, change_scale)
            writer.grab_frame()
    print(f"saved out/{ANIMATION}")

    draw_grid(axes, months, profiles, 0.62, parameters, change_scale)
    figure.savefig(OUT / STILL, dpi=150, facecolor=figure.get_facecolor())
    print(f"saved out/{STILL}")
    plt.close(figure)


if __name__ == "__main__":
    main()
