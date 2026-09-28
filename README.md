# Tide Traces — San Francisco, one month, moving

San Francisco Bay does not simply fill and empty. The sea rises and falls with
the pull of the Moon and Sun, while wind, air pressure and the shape of the bay
change what a tide gauge actually sees. This project takes one month of those
six-minute observations, lets each reading grow into a flowing thread, and
plays August 2026 back as a slowly changing tidal field.

It is a data visualisation of one natural phenomenon: 7,440 measured water
levels, one committed raw file, and a picture that cannot be drawn by hand.

**Interactive page:** [Tide Traces](https://yinuozhang0210.github.io/Tides-and-Currents/)
lets you choose a UTC date and reshape the live field. It is rebuilt from the
committed data on every push after GitHub Pages is enabled.

![Tide Traces: San Francisco water levels through August 2026](out/tide-traces-2026-08.gif)

![Still frame from the Tide Traces animation](out/tide-traces-still.png)

## The phenomenon

Tidal height is the height of the water surface relative to a local reference
level. At San Francisco it usually cycles through high and low water about
twice a day, but the height reached and the speed of the rise or fall change
through the month. I used this dataset because a normal line chart makes that
regularity easy to read, while the animation makes the repeated, uneven pulse
of the water the subject of the image.

## The source

The [NOAA CO-OPS Data API](https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=20260801&end_date=20260831&station=9414290&product=water_level&datum=MLLW&time_zone=gmt&units=metric&application=TidesAndCurrentsAssignment&format=json)
publishes observed water levels for San Francisco station 9414290. Its response
is committed unchanged as
[`data/noaa-san-francisco-water-level-2026-08.json`](data/noaa-san-francisco-water-level-2026-08.json):
7,440 rows, one observed reading every six minutes from 1 to 31 August 2026.
Each row has `t` (UTC time), `v` (water level in metres above Mean Lower Low
Water / MLLW), `s` (sample standard deviation), `f` (quality flags), and `q`
(quality status). `fetch.py` downloads the reply only when that file is absent;
afterwards, all rendering happens locally from `data/`.

## The pictures

| File | What it is |
| --- | --- |
| `out/tide-traces-2026-08.gif` | 744 frames: every UTC day appears in 24 hourly steps, revealing its six-minute records in order. |
| `out/tide-traces-still.png` | A still frame for GitHub and for seeing the visual system without waiting for the animation. |

**What the pictures show:** when a reading occurs around the circular clock;
whether its level is relatively low (teal) or high (gold); and how the water is
rising or falling, through the direction of each curved thread. New records are
bright and carry a small moving particle; each record fades independently for
48 hours, so the previous days remain only as dark traces.

**What they hide:** the usual time axis, exact water levels, the station's
geographic setting, and the physical reason for each small change. The curves
are not measured currents and the particle is not another NOAA variable: both
are an interpretation of timestamp, height and six-minute change. This is an
artwork about the record, not a chart to use for navigation.

## How it works

Three small transformations and a loop make the image:

- `observations()` reads all five NOAA fields without changing the raw file.
- `day_stats()` derives the daily mean and tidal range; these set the spread of
  the field and the background ripple shape.
- `filament_collections()` turns one row into a curved thread: `t` sets its
  starting angle, `v` sets its radius, reach, width and colour, and the
  difference from the previous `v` sets its bend. `f` and `q` reduce opacity
  when a record is not fully verified. `s` is read but not drawn, because every
  value in this file is the same (`0.028`).

`main()` loops through 31 days and 24 release times per day. A thread is drawn
until it is two days old, but its opacity drops sharply after the first day;
this makes a cross-midnight transition without one whole day suddenly vanishing.

## Run

```bash
uv run plot.py
```
