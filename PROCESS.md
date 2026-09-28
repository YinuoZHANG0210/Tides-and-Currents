# Process

This visualisation was developed with OpenAI Codex. The assignment asks for
honesty about that collaboration, so this records what the model did and what I
changed after running and looking at the result.

**What the assistant did.** Codex helped choose the NOAA CO-OPS endpoint, wrote
the first versions of `fetch.py`, `plot.py` and `web.py`, and suggested the flowing-thread
visual language after I supplied the ShaderToy references. It also helped read
the raw JSON, make the GIF and still PNG, and draft the documentation. Python
with `requests` saves the source reply; Matplotlib and Pillow render the final
files. The final plotting script has no network request: it reads only the
committed JSON in `data/`.

**What I corrected.** The first animation held the previous day as one faded
image. At midnight that image became dark all at once, although its 240 records
had happened at different times. I changed the renderer to keep an age for each
record instead: a thread is born at its actual six-minute timestamp, fades
continuously, is already very dark after one day, and is removed after two.
I also checked the raw rows against the code: the available fields are `t`,
`v`, `s`, `f`, and `q`; all 7,440 rows parse, so no missing rows are silently
discarded.

**One thing kept, and why.** I kept the decision to let `v` control several
related properties — radius, length, thickness and the teal-to-gold scale — and
to let the difference between adjacent values bend the thread. That gives the
image a water-like motion without inventing a current-speed column: every
visible line still begins with a real water-level observation.

**One thing rejected, and why.** I rejected mapping `s` to random jitter. All
7,440 `s` values are `0.028`, so drawing different noise from it would make the
image look data-driven when it is not. I kept `s` in the parser and stated in
the README that it has no visual encoding. I also did not copy the ShaderToy
GLSL, simulation buffers, textures or assets; its contribution was only the
idea of long, flowing trails.
