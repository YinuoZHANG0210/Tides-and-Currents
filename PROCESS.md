# Process

## Tools

I used the NOAA CO-OPS Data API to choose a public, no-login source of measured
water levels. The `fetch.py` script was written with help from OpenAI Codex and
downloads that reply only if the committed JSON file is missing. I used Python,
Matplotlib and Pillow in `plot.py` to parse the JSON and render a GIF and a
still PNG locally. I also used Codex to inspect field definitions and to discuss
possible visual mappings. A ShaderToy work, *Land Tide*, was a visual reference
for the idea of flowing threads and trails; I did not copy its GLSL code,
simulation, textures, or assets. Codex drafted much of the Python renderer; I
checked its field names against the raw JSON, tested it locally, and iterated
the mappings and visual result through repeated changes. The final renderer
reads only `data/` when it runs.

## Kept

I kept the proposal to use the water level itself in several related visual
properties: height controls each thread's reach, thickness and colour, while
the difference between adjacent six-minute readings bends the thread. This made
the animation feel like moving water but still made every visible thread depend
on a real NOAA observation. I also kept the decision to show the previous day
as a faint, dissolving layer because it makes the transition between dates feel
continuous instead of resetting the image at midnight.

## Rejected

I rejected a suggestion to map `s`, NOAA's sample standard deviation, to random
jitter. After checking the raw file, every `s` value is exactly `0.028`, so it
would not distinguish any observation and would only pretend to be data-driven.
I also rejected directly adapting the ShaderToy fluid solver: it needs multiple
feedback buffers and textures that are not part of this dataset, and copying it
would make the visual logic difficult to explain. Instead, the particle dashes,
long curves and ripple background are generated from the time, water level,
level change, daily mean and daily range in the committed JSON.
