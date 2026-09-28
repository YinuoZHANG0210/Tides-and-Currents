# Tidal mycelium — San Francisco water levels

![Animated tidal mycelium for August 2026](out/tidal-mycelium-2026-08.gif)

![Still frame from the tidal-mycelium animation](out/tidal-mycelium-still.png)

## The phenomenon

At San Francisco, the sea surface rises and falls as the gravitational pull of
the Moon and Sun moves water through the bay. Wind, air pressure, weather and
the shape of the coastline also affect the observed height. I chose one month
of this motion because it has a clear repeating rhythm but its range and rate
of change still differ from day to day; that makes it suitable for a slow,
time-based visualisation rather than a single summary number.

## The source

The committed raw file is the unchanged response from the
[NOAA CO-OPS Data API](https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=20260801&end_date=20260831&station=9414290&product=water_level&datum=MLLW&time_zone=gmt&units=metric&application=TidesAndCurrentsAssignment&format=json)
for San Francisco station 9414290. `data/noaa-san-francisco-water-level-2026-08.json`
contains 7,440 six-minute observed water-level records from 1–31 August 2026:
each row is one UTC observation with `t` (time), `v` (water level in metres
above Mean Lower Low Water / MLLW), `s` (sample standard deviation), `f`
(quality flags), and `q` (quality status).

## What the picture shows

The GIF releases the 240 six-minute readings of each UTC day hour by hour as a
circular field of long threads. Timestamp determines where and when a thread
appears; water level determines its reach, thickness and teal-to-gold colour;
the adjacent six-minute level change bends it, while each thread fades over 48
hours. The image hides the normal Cartesian time axis, geographic location,
exact numeric values and the individual physical causes of variation, so it is
an interpretation of the data rather than a navigation chart.

## Data-to-image mapping

| NOAA value | Visual use |
| --- | --- |
| `t` — UTC timestamp | Position around the circular clock and emergence order. |
| `v` — water level, m above MLLW | Source radius, trail reach, line width, and teal-to-gold colour. |
| Adjacent `v` values | Their six-minute difference controls the signed curve bend; a rising value also gains a cyan tint. This is not measured current direction. |
| Daily mean and range of `v` | Derived values controlling field spread and the scale and distortion of background ripples. |
| `f` — quality flags | A non-zero flag makes that record's thread much fainter. |
| `q` — quality status | Verified readings are clearer. All rows here are `v`, so this channel does not vary in this file. |
| `s` — sample standard deviation | Read but not mapped: every row has the same `0.028` value, so it cannot create meaningful variation. |

The bright particle dash and the 48-hour fade use a record's timestamp and
animation age; they are visual devices, not further measurements.

## Run

```bash
uv run plot.py
```
