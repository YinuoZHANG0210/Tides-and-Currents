# Process

This repository was developed with OpenAI Codex. The assignment asks for
honesty about that collaboration, so this records what the model proposed and
what changed after I ran the scripts and inspected the images.

**What the assistant did.** Codex helped select the NOAA CO-OPS endpoint and
wrote first versions of `fetch.py`, `plot.py`, and `web.py` from the brief: one
month of San Francisco water-level records as a flowing, circular animation. It
also suggested the long-trail visual language after I supplied ShaderToy
references, helped inspect the raw JSON, and drafted documentation. Python
`requests` saves the one raw reply; Matplotlib and Pillow render the GIF and
still; plain browser Canvas makes the interactive page. The finished renderers
do not make a network request: they read the committed JSON in `data/`.

**What I corrected.** The first renderer kept the preceding day as one faded
image. At midnight all 240 old observations changed brightness together, even
though they occurred six minutes apart across the day. I replaced that shortcut
with a per-record age: each trace is born at its actual timestamp, becomes very
dark after one day, and disappears only when it reaches two days old. I also
checked the raw records against the code: the available fields are `t`, `v`,
`s`, `f`, and `q`; all 7,440 parse, and no missing rows are silently dropped.

**One thing kept, and why.** I kept the decision to let `v` control several
linked properties — radius, reach, line width, and teal-to-gold colour — while
the difference between adjacent `v` values controls signed bend. This produces
a water-like rhythm without inventing a current-speed column: every visible
trace still starts with a real water-level observation and the mapping is
written down in the README.

**One thing rejected, and why.** I rejected mapping `s` to random jitter. Every
`s` value is `0.028`; making different noise from a constant field would make
the picture look data-driven when it is not. I kept `s` in the parser and stated
why it has no visual encoding. I also rejected copying the ShaderToy GLSL,
simulation buffers, textures, or assets: its contribution is a visual reference
for the length and flow of the traces, not code or image material in this repo.
