# Process

This repository was made with OpenAI Codex, an AI assistant. The assignment
asks for the same honesty as the worked example, so this explains what it
wrote, what I kept, and what I changed after running the code and looking at
the output.

**What the assistant did.** It helped choose the NOAA CO-OPS water-level
endpoint, wrote the first versions of fetch.py, plot.py, and web.py, and
drafted documentation from the raw JSON. It also turned my visual references
for long flowing traces into Matplotlib and Canvas code. Requests downloads the
public JSON replies; Matplotlib and Pillow render the GIF and still; the browser
page is plain Canvas. All renderers read cached data/ files after the first
fetch.

**One thing kept, and why.** I kept the readable field transformation from the
first August experiment: t puts a line around a circular clock, v gives it
reach and brightness, and the difference between adjacent v values gives it a
signed bend. It makes movement from a water-level series without inventing
current speed or direction. I extended it with month_profiles(), a short
function that calculates a month's mean, full span, and average daily range.
Those measurements determine field size and the ranked monthly line colour.

**One thing revised after testing the page.** The first web layout gave the
twelve monthly fields too nearly equal a role. It was difficult to tell which
month the date control had selected, and a title saying `LIVE MONTH LOOP` did
not say where the animation was within that month. I kept the twelve-month
comparison, but changed the interaction into a foreground/background view:
clicking a small month, or selecting it in the control, brings it to the
centre as the large bright field; the other eleven become small dim previews
around it. In live mode the heading now reports `LIVE DAY 01 / 31` (with the
appropriate day count), so the changing drawing has an explicit temporal
position. Selecting a UTC date fixes the centre field to that day while its
time-of-day trace continues and the other months continue their own loops.

**One thing rejected, and why.** The first annual version placed twelve months
as concentric rings. That made a year-shaped graphic, but it hid the individual
monthly flow fields I wanted to compare. I replaced it with a 3 × 4 grid where
every month loops independently. I also rejected a fixed calendar rainbow:
the current cyan-to-red line palette is ranked from each month's measured mean
water level and tidal energy. Finally, the first parser assumed every s field
was numeric; one real NOAA record has an empty s. It now retains that row as a
missing value instead of silently dropping it.
