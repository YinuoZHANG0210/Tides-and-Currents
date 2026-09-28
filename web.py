# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Build a self-contained interactive version of the tidal field.

    uv run web.py

The page and the existing GIF/PNG previews are written to site/. It embeds the
committed NOAA JSON, so the finished page makes no remote network request and
is ready for GitHub Pages.
"""

import json
import shutil
from pathlib import Path


HERE = Path(__file__).parent
DATA = HERE / "data" / "noaa-san-francisco-water-level-2026-08.json"
SITE = HERE / "site"
PAGE = SITE / "index.html"
ASSETS = SITE / "assets"
ANIMATION = HERE / "out" / "tide-traces-2026-08.gif"
STILL = HERE / "out" / "tide-traces-still.png"


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tide Traces — San Francisco</title>
  <style>
    :root { color-scheme: dark; --ink: #e8f2ef; --muted: #79939a; --cyan: #75cad1; --panel: #08131b; }
    * { box-sizing: border-box; }
    body { height: 100vh; margin: 0; min-width: 320px; overflow: hidden; background: #03090e; color: var(--ink); font: 15px/1.45 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { display: grid; grid-template-rows: auto minmax(0, 1fr) auto; gap: 12px; width: min(1380px, calc(100% - 40px)); height: 100vh; margin: 0 auto; padding: 18px 0 12px; }
    header { display: flex; gap: 24px; align-items: end; justify-content: space-between; min-height: 51px; }
    .eyebrow { margin: 0 0 5px; color: var(--cyan); font-size: 11px; font-weight: 750; letter-spacing: .15em; }
    h1 { margin: 0; font-weight: 650; letter-spacing: -.035em; font-size: clamp(27px, 3.4vw, 45px); line-height: 1; }
    .lede { max-width: 360px; margin: 0; color: var(--muted); font-size: 13px; }
    .panel { display: grid; grid-template-columns: minmax(0, 1fr) 274px; min-height: 0; gap: 16px; align-items: stretch; }
    .canvas-wrap { position: relative; min-height: 0; height: 100%; overflow: hidden; border: 1px solid rgba(117,202,209,.2); border-radius: 18px; background: #040b12; box-shadow: 0 26px 70px rgba(0,0,0,.25); }
    canvas { position: absolute; inset: 0; width: 100%; height: 100%; }
    .readout { position: absolute; left: 24px; top: 22px; pointer-events: none; }
    .readout p { margin: 0; }
    #date-label { font-size: clamp(22px, 4vw, 38px); font-weight: 700; letter-spacing: .03em; }
    #clock { color: var(--cyan); font-size: 12px; font-weight: 750; letter-spacing: .13em; }
    #mode { margin-top: 5px; color: var(--muted); font-size: 9px; font-weight: 750; letter-spacing: .13em; }
    .key { position: absolute; bottom: 22px; left: 24px; display: flex; gap: 12px; color: var(--muted); font-size: 11px; letter-spacing: .08em; }
    .key i { display: inline-block; width: 31px; height: 2px; margin: 0 6px 4px 0; background: linear-gradient(90deg, #0d566c, #f5b451); vertical-align: middle; }
    aside { display: flex; flex-direction: column; min-height: 0; gap: 10px; padding: 16px; border: 1px solid rgba(117,202,209,.16); border-radius: 18px; background: linear-gradient(150deg, rgba(13,35,45,.88), var(--panel)); }
    aside h2 { margin: 0 0 2px; color: var(--cyan); font-size: 11px; letter-spacing: .14em; }
    label { display: grid; gap: 7px; color: var(--muted); font-size: 12px; }
    select, button { width: 100%; appearance: none; border: 1px solid rgba(117,202,209,.34); border-radius: 9px; background: #071017; color: var(--ink); padding: 10px; font: inherit; }
    button { cursor: pointer; color: var(--cyan); font-weight: 700; }
    button:hover, select:hover { border-color: var(--cyan); }
    input[type="range"] { width: 100%; accent-color: var(--cyan); }
    .value { color: var(--ink); font-variant-numeric: tabular-nums; }
    .previews { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .preview { position: relative; display: block; overflow: hidden; border: 1px solid rgba(117,202,209,.22); border-radius: 9px; background: #040b12; aspect-ratio: 1; }
    .preview:hover { border-color: var(--cyan); }
    .preview img { display: block; width: 100%; height: 100%; object-fit: cover; }
    .preview span { position: absolute; right: 7px; bottom: 6px; padding: 2px 5px; border-radius: 4px; background: rgba(3,9,14,.78); color: var(--ink); font-size: 9px; font-weight: 750; letter-spacing: .1em; }
    .note { margin: 0; color: var(--muted); font-size: 11px; }
    .note strong { color: var(--ink); font-weight: 650; }
    footer { margin: 0 2px; color: var(--muted); font-size: 11px; }
    @media (max-width: 760px) { body { height: auto; overflow: auto; } main { display: block; width: min(100% - 24px, 600px); height: auto; padding: 18px 0 26px; } header { display: block; } .lede { margin-top: 14px; } .panel { display: grid; grid-template-columns: 1fr; margin-top: 16px; } .canvas-wrap { min-height: 86vw; } aside { display: grid; grid-template-columns: 1fr 1fr; } .previews, .note { grid-column: 1 / -1; } footer { margin-top: 16px; } }
  </style>
</head>
<body>
  <main>
    <header>
      <div><p class="eyebrow">NOAA 9414290 · WATER LEVEL · MLLW</p><h1>Tide Traces</h1></div>
      <p class="lede">San Francisco water levels, August 2026. Select a day and reshape the flow while the day unfolds.</p>
    </header>
    <section class="panel" aria-label="Interactive tidal visualisation">
      <div class="canvas-wrap">
        <canvas id="field" aria-label="Animated field of San Francisco water-level observations"></canvas>
        <div class="readout"><p id="date-label"></p><p id="clock"></p><p id="mode">LIVE LOOP · 24 HOURLY FRAMES</p></div>
        <div class="key"><span><i></i>LOW → HIGH WATER</span></div>
      </div>
      <aside>
        <h2>CONTROL FIELD</h2>
        <label>UTC date<select id="date" aria-label="Choose a UTC date"></select></label>
        <label>Line form <span class="value" id="contrast-value">1.00×</span><input id="contrast" type="range" min="0.45" max="2.10" step="0.05" value="1" aria-label="Adjust line length and twist"></label>
        <label>Flow speed <span class="value" id="speed-value">1.00×</span><input id="speed" type="range" min="0.45" max="1.60" step="0.05" value="1" aria-label="Adjust animation speed"></label>
        <button id="pause" type="button">PAUSE FLOW</button>
        <div class="previews" aria-label="Previous generated outputs">
          <a class="preview" href="assets/tide-traces-2026-08.gif" target="_blank"><img src="assets/tide-traces-2026-08.gif" alt="Generated Tide Traces animation"><span>GIF</span></a>
          <a class="preview" href="assets/tide-traces-still.png" target="_blank"><img src="assets/tide-traces-still.png" alt="Generated Tide Traces still image"><span>STILL</span></a>
        </div>
        <p class="note"><strong>Data mapping.</strong> Time places a thread on the clock; water level sets its reach, width and colour; its six-minute change sets its bend. <strong>Line form</strong> changes only length and twist, not brightness.</p>
      </aside>
    </section>
    <footer>7,440 six-minute NOAA observations · no network request after this page is built</footer>
  </main>
  <script>
    const DATA = __DATA__;
    const dates = Object.keys(DATA.days);
    const levels = dates.flatMap(date => DATA.days[date].map(row => row[1]));
    const levelMin = Math.min(...levels), levelMax = Math.max(...levels);
    const ranges = dates.map(date => dayStats(DATA.days[date]).range);
    const rangeMin = Math.min(...ranges), rangeMax = Math.max(...ranges);
    const changes = dates.flatMap(date => DATA.days[date].slice(1).map((row, i) => row[1] - DATA.days[date][i][1]));
    const changeScale = Math.max(...changes.map(Math.abs));

    const canvas = document.querySelector('#field');
    const context = canvas.getContext('2d');
    const dateInput = document.querySelector('#date');
    const contrastInput = document.querySelector('#contrast');
    const contrastValue = document.querySelector('#contrast-value');
    const speedInput = document.querySelector('#speed');
    const speedValue = document.querySelector('#speed-value');
    const pauseButton = document.querySelector('#pause');
    const dateLabel = document.querySelector('#date-label');
    const clockLabel = document.querySelector('#clock');
    const DAY_DURATION = 18000;
    let selected = 0, formContrast = 1, speed = 1, running = true, started = performance.now(), frozenProgress = 0;

    for (const date of dates) {
      const option = document.createElement('option');
      option.value = date;
      option.textContent = new Date(`${date}T00:00:00Z`).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }).toUpperCase();
      dateInput.append(option);
    }
    dateInput.addEventListener('change', () => { selected = dates.indexOf(dateInput.value); started = performance.now(); frozenProgress = 0; });
    contrastInput.addEventListener('input', () => { formContrast = Number(contrastInput.value); contrastValue.textContent = `${formContrast.toFixed(2)}×`; });
    speedInput.addEventListener('input', () => {
      const now = performance.now();
      const progress = running ? cycleAt(now) : frozenProgress;
      speed = Number(speedInput.value); speedValue.textContent = `${speed.toFixed(2)}×`;
      started = now - progress * DAY_DURATION / speed; frozenProgress = progress;
    });
    pauseButton.addEventListener('click', () => {
      running = !running;
      if (!running) frozenProgress = cycleAt(performance.now());
      else started = performance.now() - frozenProgress * DAY_DURATION / speed;
      pauseButton.textContent = running ? 'PAUSE FLOW' : 'RESUME FLOW';
    });

    function clamp(value, low = 0, high = 1) { return Math.max(low, Math.min(high, value)); }
    function smooth(value) { value = clamp(value); return value * value * (3 - 2 * value); }
    function mix(a, b, t) { return a.map((value, i) => value + (b[i] - value) * t); }
    function rgba(rgb, alpha) { return `rgba(${rgb.map(value => Math.round(value)).join(',')},${clamp(alpha, 0, 1)})`; }
    function colour(levelFraction, rising, freshness) {
      const base = mix([8, 64, 82], [245, 184, 78], levelFraction);
      const tinted = rising ? mix(base, [61, 232, 235], .30) : base;
      return mix(tinted, [235, 249, 242], .10 + .48 * freshness);
    }
    function dayStats(day) {
      const values = day.map(row => row[1]);
      const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
      return { mean, range: Math.max(...values) - Math.min(...values) };
    }
    function cycleAt(now) { return ((now - started) * speed % DAY_DURATION) / DAY_DURATION; }
    function frameRelease(progress) { return (Math.floor(progress * 24) + 1) / 24; }
    function resize() {
      const box = canvas.getBoundingClientRect();
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(box.width * ratio); canvas.height = Math.round(box.height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      return box;
    }
    let bounds = resize();
    new ResizeObserver(() => { bounds = resize(); }).observe(canvas);

    function point(x, y, scale, cx, cy) { return [cx + x * scale, cy + y * scale]; }
    function drawRipples(stats, release, scale, cx, cy) {
      const meanFraction = (stats.mean - levelMin) / (levelMax - levelMin);
      const rangeFraction = (stats.range - rangeMin) / (rangeMax - rangeMin || 1);
      context.save();
      for (let ring = 0; ring < 7; ring++) {
        const baseRadius = .34 + ring * .14 + .24 * rangeFraction;
        const amplitude = .010 + (.014 + .020 * rangeFraction) * (ring + 1) / 7;
        context.beginPath();
        for (let step = 0; step <= 120; step++) {
          const angle = Math.PI * 2 * step / 120;
          const wave = Math.sin((2 + ring % 3) * angle - release * Math.PI * 2);
          const cross = .45 * Math.sin((5 + ring) * angle + meanFraction * Math.PI * 2);
          const radius = baseRadius + amplitude * (wave + cross);
          const [x, y] = point(radius * Math.cos(angle), radius * Math.sin(angle), scale, cx, cy);
          step ? context.lineTo(x, y) : context.moveTo(x, y);
        }
        context.strokeStyle = `rgba(36,166,196,${.13 + .04 * rangeFraction})`;
        context.lineWidth = .45 + ring * .16;
        context.stroke();
      }
      context.restore();
    }

    function drawDay(day, stats, release, dayOffset, scale, cx, cy) {
      const meanFraction = (stats.mean - levelMin) / (levelMax - levelMin);
      const rangeFraction = (stats.range - rangeMin) / (rangeMax - rangeMin || 1);
      const spread = .46 + .82 * Math.pow(rangeFraction, .72);
      const core = .13 + .25 * (1 - rangeFraction) + .06 * (1 - meanFraction);
      for (let slot = 0; slot < day.length; slot++) {
        const row = day[slot], timeFraction = slot / (day.length - 1);
        const age = dayOffset + release - timeFraction;
        if (age < -.002 || age >= 2) continue;
        const arrival = dayOffset === 0 ? smooth((release - timeFraction + .018) * 24 * 1.5) : 1;
        const persistence = Math.pow(1 - clamp(age / 2), 2.60);
        const freshness = Math.exp(-2.40 * Math.max(age, 0));
        const levelFraction = clamp((row[1] - levelMin) / (levelMax - levelMin));
        const previous = day[Math.max(0, slot - 1)][1];
        const change = clamp((row[1] - previous) / changeScale, -1, 1);
        const baseAngle = Math.PI * 2 * timeFraction - Math.PI / 2 + .70 * (meanFraction - .5);
        const radius = core + (.14 + .42 * levelFraction) * spread;
        // This is the interactive control: it exaggerates the geometry of the
        // data-derived trail, without altering its data-derived colour or alpha.
        const lengthFactor = .58 + .42 * formContrast;
        const twistFactor = .45 + .55 * formContrast;
        const reach = (.18 + .70 * levelFraction) * spread * (.25 + .75 * arrival) * lengthFactor;
        const curl = .16 + .86 * change * twistFactor;
        const sweep = (.34 + .44 * levelFraction + .52 * Math.abs(change)) * (change >= 0 ? 1 : -1) * twistFactor;
        const drift = .08 * Math.sin(Math.PI * 2 * (release - timeFraction));
        const wiggle = (.028 + .048 * rangeFraction) * twistFactor;
        const flagged = row[2] !== '0,0,0,0';
        const quality = row[3] === 'v' ? .76 : .30;
        const alpha = quality * persistence * arrival * (.62 + .38 * freshness) * (flagged ? .18 : 1);
        const rgb = colour(levelFraction, change >= 0, freshness);
        const width = (.09 + .48 * levelFraction) * (.72 + .48 * rangeFraction);
        const points = [];
        for (let step = 0; step < 42; step++) {
          const progress = step / 41;
          const wave = Math.sin(slot * .19 + step * .64 + release * Math.PI * 2);
          const eddy = Math.sin(slot * .07 - step * .31 + release * Math.PI);
          const angle = baseAngle + (curl + drift) * progress + sweep * Math.pow(progress, 1.28) + wiggle * wave;
          const distance = radius + reach * progress + wiggle * 1.8 * eddy * (1 - progress * .35);
          points.push(point(distance * Math.cos(angle), distance * Math.sin(angle), scale, cx, cy));
        }
        context.beginPath();
        points.forEach(([x, y], i) => i ? context.lineTo(x, y) : context.moveTo(x, y));
        context.strokeStyle = rgba(rgb, alpha * .11); context.lineWidth = width + 1.15; context.lineCap = 'round'; context.stroke();
        context.beginPath();
        points.forEach(([x, y], i) => i ? context.lineTo(x, y) : context.moveTo(x, y));
        context.strokeStyle = rgba(rgb, alpha); context.lineWidth = Math.max(.45, width); context.stroke();
        const particle = Math.floor(((release * 1.6 + timeFraction * .35) % 1) * (points.length - 2));
        context.beginPath(); context.moveTo(...points[particle]); context.lineTo(...points[particle + 1]);
        context.strokeStyle = rgba([244, 255, 248], alpha * (.35 + .65 * freshness)); context.lineWidth = Math.max(1.2, width + 1.05); context.stroke();
      }
    }

    function render(now) {
      const release = frameRelease(running ? cycleAt(now) : frozenProgress);
      const width = bounds.width, height = bounds.height, size = Math.min(width, height);
      const cx = width / 2, cy = height / 2 + 8, scale = size / 4.25;
      context.clearRect(0, 0, width, height);
      context.fillStyle = '#040b12'; context.fillRect(0, 0, width, height);
      const day = DATA.days[dates[selected]], stats = dayStats(day);
      drawRipples(stats, release, scale, cx, cy);
      for (const offset of [2, 1]) if (selected - offset >= 0) drawDay(DATA.days[dates[selected - offset]], dayStats(DATA.days[dates[selected - offset]]), release, offset, scale, cx, cy);
      drawDay(day, stats, release, 0, scale, cx, cy);
      dateLabel.textContent = new Date(`${dates[selected]}T00:00:00Z`).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }).toUpperCase();
      const minutes = Math.min(1439, Math.round(release * 24) * 60);
      clockLabel.textContent = `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')} UTC · MEAN ${stats.mean.toFixed(2)} M · RANGE ${stats.range.toFixed(2)} M`;
      requestAnimationFrame(render);
    }
    requestAnimationFrame(render);
  </script>
</body>
</html>
"""


def compact_data(path):
    """Keep the fields the interactive renderer uses, grouped by UTC date."""
    with path.open(encoding="utf-8") as handle:
        reply = json.load(handle)

    days = {}
    for row in reply["data"]:
        date, clock = row["t"].split(" ")
        minutes = int(clock[:2]) * 60 + int(clock[3:])
        days.setdefault(date, []).append([minutes, float(row["v"]), row["f"], row["q"]])
    return json.dumps({"days": days}, separators=(",", ":"))


def main():
    SITE.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    for source in (ANIMATION, STILL):
        shutil.copy2(source, ASSETS / source.name)
    PAGE.write_text(HTML.replace("__DATA__", compact_data(DATA)), encoding="utf-8")
    print(f"saved {PAGE.relative_to(HERE)} and previews from {DATA.relative_to(HERE)}")


if __name__ == "__main__":
    main()
