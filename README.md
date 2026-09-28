# Tide Traces — San Francisco, one month, moving

San Francisco Bay does not simply fill and empty. The water rises and falls
with the pull of the Moon and Sun, while wind, air pressure and the geometry of
the bay change what the tide gauge receives. This repository takes one month of
six-minute water-level observations, turns every reading into a flowing trace,
and plays August 2026 back as a slowly changing tidal field.

It is one published file of measurements about a natural phenomenon, two
rendered pictures, and an optional interactive page made from the same numbers.

![Tide Traces: San Francisco water levels through August 2026](out/tide-traces-2026-08.gif)

![Still frame from the Tide Traces animation](out/tide-traces-still.png)

**The interactive page:** <https://yinuozhang0210.github.io/Tides-and-Currents/>
— choose a UTC date, alter the trail form, and change the speed.

## The phenomenon

Tidal height is the height of the water surface relative to a local reference
level. San Francisco normally passes through high and low water about twice a
day, but neither the height reached nor the speed of the rise and fall is the
same every day. A line chart makes that periodicity easy to read; this animation
uses its repeating but uneven pulse as the subject of the picture instead.

## The source

[NOAA Tides and Currents](https://tidesandcurrents.noaa.gov/), operated by the
Center for Operational Oceanographic Products and Services (CO-OPS), publishes
observed water levels for San Francisco station 9414290. Its `water_level`
product is returned as JSON; this endpoint asks for one month, MLLW as the
vertical datum, GMT as the time zone, and metric units:

```text
https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=20260801&end_date=20260831&station=9414290&product=water_level&datum=MLLW&time_zone=gmt&units=metric&application=TidesAndCurrentsAssignment&format=json
```

One reply covers the whole month. It contains 7,440 readings: one observed
water level every six minutes from 1 to 31 August 2026, at one tide gauge. Each
JSON item has `t` (UTC timestamp), `v` (water level in metres above Mean Lower
Low Water / MLLW), `s` (sample standard deviation), `f` (quality flags), and
`q` (quality status). `fetch.py` makes exactly this one request only if the
target file is absent, then saves the reply byte-for-byte as
[`data/noaa-san-francisco-water-level-2026-08.json`](data/noaa-san-francisco-water-level-2026-08.json).
Once that committed file exists, every picture and web page runs only from
`data/`, with the internet off.

## The pictures

| Command | Makes | What it is |
| --- | --- | --- |
| `uv run plot.py` | `out/tide-traces-2026-08.gif`, `out/tide-traces-still.png` | A 744-frame GIF: 31 UTC days × 24 hourly releases. Each frame adds the readings that have occurred so far that day. |
| `uv run web.py` | `site/index.html` | The same data and visual rules as an interactive Canvas page: select one UTC date, change the trails' length and twist, and alter playback speed. |

The GIF is deliberately slow enough to make one day legible before the next
date arrives. The still is the frame with the largest daily tidal range, so the
README also shows the full visual system when animation is not playing.

**What the pictures show:** Each trace's position around the circular clock
places an observation in the day, its teal-to-gold colour turns low-to-high
water into light, and its signed bend gives a rising or falling level a visible
gesture. A new reading arrives as a bright particle and then fades over 48
hours, so midnight becomes an overlap of the present tide and a dim memory of
the days before it. **What they hide:** Instead of preserving a gauge chart's
axes, exact labels, map location, and physical explanations, the work turns
time, height, and six-minute change into a field of marks; its smooth arcs,
moving particle, and adjustable `Line form` are an expressive language for
water's rhythm, not a claim to show measured current paths.

## How it works

Three functions, each a transformation, and a loop make the image:

- `observations()` reads all 7,440 JSON observations and retains the five NOAA
  fields used by the renderer.
- `day_stats()` derives one day's mean level and tidal range. Those derived
  values set the field's spread and the size of the background ripples.
- `filament_collections()` turns one record into a trace: `t` gives its starting
  angle, `v` gives radius, reach, width and colour, and the difference from the
  previous `v` gives the signed bend. `f` and `q` reduce opacity for a flagged
  or non-verified observation; `s` is read but not encoded because every value
  in this file is `0.028`.

`main()` loops through 31 days and 24 release times per day. The same
calculation is expressed in browser JavaScript by `web.py`; it writes a
self-contained `site/index.html` and copies the two rendered preview files
into `site/assets/`. `site/` is output and is never committed.

## Run

```bash
uv run plot.py
```
