# Process

## Tools

I used the NOAA CO-OPS Data API as a public source of observed water levels.
`fetch.py` uses Python `requests` to save the raw API reply only when the JSON
file is missing; after it is committed, `plot.py` works offline from `data/`.
I used Python, Matplotlib and Pillow to read the JSON and make the GIF and
still PNG. I used OpenAI Codex to help draft most of the plotting code, inspect
the raw field definitions, and iterate on the visual mapping. A ShaderToy work,
*Land Tide*, was a visual reference for flowing trails; I did not copy its
GLSL, feedback simulation, textures or assets.

The main correction I made to the drafted renderer was its treatment of time.
Its first version retained the previous day as one faint raster snapshot, so
all old lines changed brightness together at midnight. I replaced that with a
per-record age calculation: each `t` value is retained and faded independently
for 48 hours. I also checked the literal raw fields (`t`, `v`, `s`, `f`, `q`)
against the JSON and confirmed that all 7,440 records parse; no field was
invented and no unparsable rows were silently dropped.

## Kept

I kept the idea of mapping water level to several linked visual properties:
`v` controls reach, thickness and colour, while the difference from the prior
six-minute `v` controls the direction and amount of bend. This was useful
because the picture gains a water-like sense of motion, but every thread still
comes from a real record and the mapping can be explained directly from the
file.

## Rejected

I rejected mapping `s` to random jitter. Inspection showed that every `s`
value in this file is `0.028`; using it to make variable noise would falsely
suggest that the variability came from the data. I kept `s` in the parser and
documented why it has no visual encoding instead.
