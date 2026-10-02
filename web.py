# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Build the interactive 3 × 4 version of the twelve-month tidal field.

    uv run web.py

The page embeds all twelve cached NOAA replies. Each tile loops independently
from the beginning to the end of its calendar month without another request.
"""

import json
import shutil
from pathlib import Path


WINDOW = [(2025, month) for month in range(10, 13)] + [(2026, month) for month in range(1, 10)]
MONTH_NAMES = ("OCT", "NOV", "DEC", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP")
HERE = Path(__file__).parent
DATA = HERE / "data"
SITE = HERE / "site"
PAGE = SITE / "index.html"
ASSETS = SITE / "assets"
ANIMATION = HERE / "out" / "tide-traces-year-2025-10-to-2026-09.gif"
STILL = HERE / "out" / "tide-traces-year-still.png"


def monthly_file(year, month):
    """Return one raw, cached NOAA reply."""
    return DATA / f"noaa-san-francisco-water-level-{year}-{month:02}.json"


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tide Traces — twelve tidal months</title>
  <style>
    :root { color-scheme:dark; --ink:#e8f3ef; --muted:#78959d; --cyan:#74cbd2; --panel:#07131b; }
    * { box-sizing:border-box; }
    body { height:100vh; min-width:320px; margin:0; overflow:hidden; background:#02080d; color:var(--ink); font:15px/1.45 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    main { display:grid; grid-template-rows:auto minmax(0,1fr) auto; gap:12px; width:min(1440px,calc(100% - 40px)); height:100vh; margin:auto; padding:18px 0 12px; }
    header { display:flex; align-items:end; justify-content:space-between; gap:28px; min-height:52px; }
    .eyebrow { margin:0 0 5px; color:var(--cyan); font-size:11px; font-weight:750; letter-spacing:.15em; }
    h1 { margin:0; font-size:clamp(28px,3.4vw,46px); font-weight:650; letter-spacing:-.04em; line-height:1; }
    .lede { max-width:420px; margin:0; color:var(--muted); font-size:13px; }
    .panel { display:grid; grid-template-columns:minmax(0,1fr) 292px; gap:16px; min-height:0; }
    .canvas-wrap { position:relative; min-height:0; overflow:hidden; border:1px solid rgba(116,203,210,.22); border-radius:18px; background:#040b12; box-shadow:0 26px 70px rgba(0,0,0,.28); }
    canvas { position:absolute; inset:0; width:100%; height:100%; cursor:crosshair; }
    .readout { position:absolute; left:24px; top:19px; pointer-events:none; }
    .readout p { margin:0; }
    #focus-label { font-size:clamp(18px,2.5vw,28px); font-weight:700; letter-spacing:.025em; }
    #clock { color:var(--cyan); font-size:10px; font-weight:750; letter-spacing:.12em; }
    .key { position:absolute; bottom:19px; left:24px; pointer-events:none; color:var(--muted); font-size:10px; letter-spacing:.08em; }
    .key i { display:inline-block; width:34px; height:2px; margin:0 6px 4px 0; background:linear-gradient(90deg,#31d8ef,#86ff68,#ffd54b,#ff7856); vertical-align:middle; }
    aside { display:flex; flex-direction:column; min-height:0; gap:10px; padding:16px; border:1px solid rgba(116,203,210,.16); border-radius:18px; background:linear-gradient(150deg,rgba(13,36,47,.92),var(--panel)); }
    aside h2 { margin:0 0 2px; color:var(--cyan); font-size:11px; letter-spacing:.14em; }
    label { display:grid; gap:7px; color:var(--muted); font-size:12px; }
    select,button { width:100%; border:1px solid rgba(116,203,210,.34); border-radius:9px; background:#061017; color:var(--ink); padding:10px; font:inherit; }
    button { cursor:pointer; color:var(--cyan); font-weight:700; }
    button:hover,select:hover { border-color:var(--cyan); }
    input[type="range"] { width:100%; accent-color:var(--cyan); }
    .value { color:var(--ink); font-variant-numeric:tabular-nums; }
    .hint,.note { margin:0; color:var(--muted); font-size:10.5px; }
    .note strong { color:var(--ink); font-weight:650; }
    .previews { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:auto; }
    .preview { position:relative; display:block; overflow:hidden; border:1px solid rgba(116,203,210,.22); border-radius:9px; background:#030a11; aspect-ratio:1; }
    .preview:hover { border-color:var(--cyan); }
    .preview img { display:block; width:100%; height:100%; object-fit:cover; }
    .preview span { position:absolute; right:7px; bottom:6px; padding:2px 5px; border-radius:4px; background:rgba(2,8,13,.8); color:var(--ink); font-size:9px; font-weight:750; letter-spacing:.1em; }
    footer { margin:0 2px; color:var(--muted); font-size:11px; }
    @media (max-width:760px) { body { height:auto; overflow:auto; } main { display:block; width:min(100% - 24px,620px); height:auto; padding:18px 0 26px; } header { display:block; } .lede { margin-top:14px; } .panel { grid-template-columns:1fr; margin-top:16px; } .canvas-wrap { min-height:92vw; } aside { display:grid; grid-template-columns:1fr 1fr; } .hint,.previews,.note { grid-column:1/-1; } footer { margin-top:16px; } }
  </style>
</head>
<body>
  <main>
    <header>
      <div><p class="eyebrow">NOAA 9414290 · WATER LEVEL · MLLW</p><h1>Tide Traces</h1></div>
      <p class="lede">87,600 observed water levels at one San Francisco gauge: twelve fields, each replaying one calendar month from first reading to last.</p>
    </header>
    <section class="panel" aria-label="Interactive twelve-month tidal visualisation">
      <div class="canvas-wrap">
        <canvas id="field" aria-label="Twelve animated months of San Francisco water-level observations"></canvas>
        <div class="readout"><p id="focus-label">OCT 2025 · FOCUS FIELD</p><p id="clock">CLICK A MONTH TO BRING IT FORWARD</p></div>
        <div class="key"><span><i></i>FOCUS MONTH LARGE · OTHER MONTHS DIMMED · LOW → HIGH WATER WITHIN EACH FIELD</span></div>
      </div>
      <aside>
        <h2>CONTROLS</h2>
        <label>Focus month<select id="month" aria-label="Choose a month field"></select></label>
        <label>UTC date<select id="date" aria-label="Choose a date in the focused month"></select></label>
        <p class="hint">Click a small surrounding month to bring it forward. Live month loop keeps all twelve moving; selecting a date freezes only the focused field.</p>
        <label>Line form <span class="value" id="contrast-value">1.00×</span><input id="contrast" type="range" min="0.45" max="2.10" step="0.05" value="1" aria-label="Adjust line length and twist"></label>
        <label>Flow speed <span class="value" id="speed-value">1.00×</span><input id="speed" type="range" min="0.45" max="1.60" step="0.05" value="1" aria-label="Adjust the monthly animation speed"></label>
        <button id="pause" type="button">PAUSE FLOW</button>
        <div class="previews" aria-label="Generated annual outputs">
          <a class="preview" href="assets/tide-traces-year-2025-10-to-2026-09.gif" target="_blank"><img src="assets/tide-traces-year-2025-10-to-2026-09.gif" alt="Generated Tide Traces twelve-month animation"><span>GIF</span></a>
          <a class="preview" href="assets/tide-traces-year-still.png" target="_blank"><img src="assets/tide-traces-year-still.png" alt="Generated Tide Traces twelve-month still image"><span>STILL</span></a>
        </div>
        <p class="note"><strong>How to read it.</strong> Time sets a line's clock angle; level sets its reach and brightness; six-minute change sets bend. Monthly mean and tidal range set each field's hue, saturation, ripple scale, and size. <strong>Line form</strong> changes geometry only.</p>
      </aside>
    </section>
    <footer>12 cached NOAA replies · 87,600 six-minute observations · 01 OCT 2025 — 30 SEP 2026 · no network request after build</footer>
  </main>
  <script>
    const SOURCE = __DATA__;
    const MONTHS = SOURCE.months.map(month => ({
      ...month,
      days: month.days.map(day => {
        const values = day.rows.map(row => row[1]);
        const sigmas = day.rows.map(row => row[2]).filter(value => value !== null);
        return { ...day,
          mean: values.reduce((sum,value) => sum+value,0)/values.length,
          range: Math.max(...values)-Math.min(...values),
          sigma: sigmas.length ? sigmas.reduce((sum,value)=>sum+value,0)/sigmas.length : null
        };
      })
    }));
    const allRows = MONTHS.flatMap(month => month.days.flatMap(day => day.rows));
    const levels = allRows.map(row => row[1]), levelMin = Math.min(...levels), levelMax = Math.max(...levels);
    const allDays = MONTHS.flatMap(month => month.days), ranges = allDays.map(day => day.range);
    const rangeMin = Math.min(...ranges), rangeMax = Math.max(...ranges);
    const monthlyMeans = MONTHS.map(month => month.days.reduce((sum,day)=>sum+day.mean,0)/month.days.length);
    const monthlySpans = MONTHS.map(month => {
      const values=month.days.flatMap(day=>day.rows.map(row=>row[1]));
      return Math.max(...values)-Math.min(...values);
    });
    const monthlyDailyRanges = MONTHS.map(month => month.days.reduce((sum,day)=>sum+day.range,0)/month.days.length);
    const PROFILES = MONTHS.map((month,index) => {
      const meanFraction=(monthlyMeans[index]-Math.min(...monthlyMeans))/(Math.max(...monthlyMeans)-Math.min(...monthlyMeans)||1);
      const spanFraction=(monthlySpans[index]-Math.min(...monthlySpans))/(Math.max(...monthlySpans)-Math.min(...monthlySpans)||1);
      const dailyRangeFraction=(monthlyDailyRanges[index]-Math.min(...monthlyDailyRanges))/(Math.max(...monthlyDailyRanges)-Math.min(...monthlyDailyRanges)||1);
      const energy=.58*spanFraction+.42*dailyRangeFraction;
      return { mean:monthlyMeans[index], span:monthlySpans[index], dailyRange:monthlyDailyRanges[index], meanFraction, energy, fieldScale:.72+.58*energy, colourSignal:.65*meanFraction+.35*energy };
    });
    [...PROFILES].sort((first,second)=>first.colourSignal-second.colourSignal).forEach((profile,rank)=>profile.colourRank=rank/(PROFILES.length-1));
    const sigmaValues = allRows.map(row=>row[2]).filter(value=>value!==null);
    const sigmaMin = Math.min(...sigmaValues), sigmaMax = Math.max(...sigmaValues);
    const changes = allRows.slice(1).map((row,index)=>row[1]-allRows[index][1]);
    const changeScale = Math.max(...changes.map(Math.abs));

    const canvas = document.querySelector('#field'), context = canvas.getContext('2d');
    const monthInput = document.querySelector('#month'), dateInput = document.querySelector('#date');
    const contrastInput = document.querySelector('#contrast'), contrastValue = document.querySelector('#contrast-value');
    const speedInput = document.querySelector('#speed'), speedValue = document.querySelector('#speed-value');
    const pauseButton = document.querySelector('#pause'), focusLabel = document.querySelector('#focus-label'), clockLabel = document.querySelector('#clock');
    const MONTH_DURATION = 120000, STEPS = 96;
    let selectedMonth=0, selectedDate=null, formContrast=1, speed=1, running=true, started=performance.now(), frozenProgress=0, lastKey='', hitAreas=[];

    function label(date) { return new Date(date+'T00:00:00Z').toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'}).toUpperCase(); }
    function resetClock() { started=performance.now(); frozenProgress=0; lastKey=''; }
    function populateMonths() {
      MONTHS.forEach((month,index) => { const option=document.createElement('option'); option.value=index; option.textContent=month.label; monthInput.append(option); });
    }
    function populateDates() {
      dateInput.replaceChildren();
      const live=document.createElement('option'); live.value='live'; live.textContent='LIVE MONTH LOOP'; dateInput.append(live);
      MONTHS[selectedMonth].days.forEach((day,index) => { const option=document.createElement('option'); option.value=index; option.textContent=label(day.date); dateInput.append(option); });
      dateInput.value='live'; selectedDate=null;
    }
    function chooseMonth(index) { selectedMonth=Number(index); monthInput.value=selectedMonth; populateDates(); resetClock(); }
    populateMonths(); chooseMonth(0);
    monthInput.addEventListener('change',()=>chooseMonth(monthInput.value));
    dateInput.addEventListener('change',()=>{ selectedDate=dateInput.value==='live' ? null : Number(dateInput.value); resetClock(); });
    contrastInput.addEventListener('input',()=>{ formContrast=Number(contrastInput.value); contrastValue.textContent=formContrast.toFixed(2)+'×'; lastKey=''; });
    speedInput.addEventListener('input',()=>{
      const now=performance.now(), progress=running ? cycleAt(now) : frozenProgress;
      speed=Number(speedInput.value); speedValue.textContent=speed.toFixed(2)+'×'; started=now-progress*MONTH_DURATION/speed; frozenProgress=progress;
    });
    pauseButton.addEventListener('click',()=>{
      running=!running;
      if(!running) frozenProgress=cycleAt(performance.now()); else started=performance.now()-frozenProgress*MONTH_DURATION/speed;
      pauseButton.textContent=running ? 'PAUSE FLOW' : 'RESUME FLOW'; lastKey='';
    });

    function clamp(value,low=0,high=1) { return Math.max(low,Math.min(high,value)); }
    function smooth(value) { value=clamp(value); return value*value*(3-2*value); }
    function mix(a,b,t) { return a.map((value,index)=>value+(b[index]-value)*t); }
    function rgba(rgb,alpha) { return 'rgba('+rgb.map(value=>Math.round(value)).join(',')+','+clamp(alpha)+')'; }
    function accent(index) {
      const profile=PROFILES[index];
      return hsv(.56-.56*profile.colourRank,.58+.32*profile.energy,.70+.25*profile.meanFraction);
    }
    function hsv(h,s,v) {
      const i=Math.floor(h*6), f=h*6-i, p=v*(1-s), q=v*(1-f*s), t=v*(1-(1-f)*s), options=[[v,t,p],[q,v,p],[p,v,t],[p,q,v],[t,p,v],[v,p,q]];
      return options[i%6].map(value=>value*255);
    }
    function colour(levelFraction,rising,monthIndex,freshness) {
      const tone=accent(monthIndex), low=mix([3,10,20],tone,.42), high=mix(tone,[255,255,255],.22);
      let base=mix(low,high,levelFraction); if(rising) base=mix(base,mix(tone,[255,237,199],.38),.12);
      return mix(base,[255,255,255],.03+.16*freshness);
    }
    function cycleAt(now) { return ((now-started)*speed%MONTH_DURATION)/MONTH_DURATION; }
    function resize() {
      const box=canvas.getBoundingClientRect(), ratio=Math.min(window.devicePixelRatio||1,2);
      canvas.width=Math.round(box.width*ratio); canvas.height=Math.round(box.height*ratio); context.setTransform(ratio,0,0,ratio,0,0); return box;
    }
    let bounds=resize(); new ResizeObserver(()=>{bounds=resize();lastKey='';}).observe(canvas);
    function point(radius,angle,scale,cx,cy) { return [cx+radius*Math.cos(angle)*scale,cy+radius*Math.sin(angle)*scale]; }
    function stroke(points,rgb,alpha,width) {
      context.beginPath(); points.forEach(([x,y],index)=>index?context.lineTo(x,y):context.moveTo(x,y));
      context.strokeStyle=rgba(rgb,alpha); context.lineWidth=width; context.lineCap='round'; context.stroke();
    }
    function stats(day) {
      return { meanFraction:(day.mean-levelMin)/(levelMax-levelMin), rangeFraction:(day.range-rangeMin)/(rangeMax-rangeMin||1) };
    }
    function drawRipples(day,release,monthIndex,scale,cx,cy,fieldOpacity) {
      const values=stats(day), rgb=accent(monthIndex), profile=PROFILES[monthIndex];
      for(let ring=0;ring<6;ring++) {
        const base=(.34+ring*.15+.24*values.rangeFraction)*profile.fieldScale, amplitude=(.010+(.014+.020*values.rangeFraction)*(ring+1)/6)*(.72+.60*profile.energy), points=[];
        for(let step=0;step<=96;step++) {
          const angle=Math.PI*2*step/96, wave=Math.sin((2+ring%3)*angle-release*Math.PI*2), cross=.45*Math.sin((5+ring)*angle+values.meanFraction*Math.PI*2);
          points.push(point(base+amplitude*(wave+cross),angle,scale,cx,cy));
        }
        stroke(points,rgb,(.045+.03*values.rangeFraction)*fieldOpacity,.22+.12*ring);
      }
    }
    function drawDay(day,release,dayOffset,monthIndex,scale,cx,cy,fieldOpacity) {
      const profile=PROFILES[monthIndex], values=stats(day), spread=(.46+.82*Math.pow(values.rangeFraction,.72))*profile.fieldScale, core=.13+.25*(1-values.rangeFraction)+.06*(1-values.meanFraction);
      for(let slot=0;slot<day.rows.length;slot+=3) {
        const row=day.rows[slot], timeFraction=slot/(day.rows.length-1), age=dayOffset+release-timeFraction;
        if(age<-.002 || age>=2) continue;
        const arrival=dayOffset===0 ? smooth((release-timeFraction+.018)*STEPS*1.5) : 1;
        const persistence=Math.pow(1-clamp(age/2),2.60), freshness=Math.exp(-2.40*Math.max(age,0));
        const levelFraction=clamp((row[1]-levelMin)/(levelMax-levelMin));
        const sigmaFraction=clamp(((row[2]===null ? sigmaMin : row[2])-sigmaMin)/(sigmaMax-sigmaMin||1));
        const change=clamp((row[1]-day.rows[Math.max(0,slot-1)][1])/changeScale,-1,1);
        const lengthFactor=.58+.42*formContrast, twistFactor=.45+.55*formContrast;
        const baseAngle=Math.PI*2*timeFraction-Math.PI/2+.70*(values.meanFraction-.5), radius=core+(.14+.42*levelFraction)*spread;
        const reach=(.24+.86*levelFraction)*spread*(.25+.75*arrival)*lengthFactor*profile.fieldScale, curl=(.16+.86*change)*twistFactor;
        const sweep=(.34+.44*levelFraction+.52*Math.abs(change))*(change>=0?1:-1)*twistFactor, drift=.08*Math.sin(Math.PI*2*(release-timeFraction)), wiggle=(.028+.048*values.rangeFraction)*twistFactor*(.78+.34*profile.energy);
        const points=[];
        for(let step=0;step<38;step++) {
          const progress=step/37, wave=Math.sin(slot*.19+step*.64+release*Math.PI*2), eddy=Math.sin(slot*.07-step*.31+release*Math.PI);
          points.push(point(radius+reach*progress+wiggle*1.8*eddy*(1-progress*.35),baseAngle+(curl+drift)*progress+sweep*Math.pow(progress,1.28)+wiggle*wave,scale,cx,cy));
        }
        let alpha=(row[4]==='v'?.76:.30)*persistence*arrival*(.62+.38*freshness); if(row[3]!=='0,0,0,0') alpha*=.18; alpha=Math.min(1,alpha*1.34)*fieldOpacity;
        const rgb=colour(levelFraction,change>=0,monthIndex,freshness), width=(.15+.68*levelFraction)*(.78+.54*values.rangeFraction);
        stroke(points,rgb,alpha*(.14+.30*sigmaFraction),width+1.25+1.20*sigmaFraction); stroke(points,rgb,alpha,Math.max(.52,width));
        const particle=Math.floor(((release*1.6+timeFraction*.35)%1)*(points.length-2));
        stroke([points[particle],points[particle+1]],[245,255,249],alpha*(.35+.65*freshness),width+1.00);
      }
    }
    function drawTile(monthIndex,progress,box,focused) {
      const month=MONTHS[monthIndex], pin=monthIndex===selectedMonth && selectedDate!==null;
      const position=pin ? selectedDate+progress : progress*month.days.length, dayIndex=Math.min(Math.floor(position),month.days.length-1);
      const release=pin ? progress : position-Math.floor(position), day=month.days[dayIndex];
      // A chosen month is a foreground field, not just a slightly larger tile:
      // it receives almost four times the drawing scale and the surrounding
      // months become a quiet, contextual calendar.
      const size=Math.min(box.w,box.h), scale=size/(focused?3.45:4.95), cx=box.x+box.w/2, cy=box.y+box.h/2;
      const fieldOpacity=focused?1:.10;
      if(focused) {
        const halo=context.createRadialGradient(cx,cy,size*.05,cx,cy,size*.66), rgb=accent(monthIndex);
        halo.addColorStop(0,rgba(rgb,.10)); halo.addColorStop(.48,rgba(rgb,.035)); halo.addColorStop(1,rgba(rgb,0));
        context.fillStyle=halo; context.fillRect(cx-size*.68,cy-size*.68,size*1.36,size*1.36);
      }
      drawRipples(day,release,monthIndex,scale,cx,cy,fieldOpacity);
      for(const offset of [2,1]) if(dayIndex-offset>=0) drawDay(month.days[dayIndex-offset],release,offset,monthIndex,scale,cx,cy,fieldOpacity);
      drawDay(day,release,0,monthIndex,scale,cx,cy,fieldOpacity);
      const rgb=accent(monthIndex);
      if(focused) {
        const hour=Math.min(24,Math.round(release*24)); context.textAlign='center'; context.fillStyle='#edf7ef'; context.font='700 20px ui-sans-serif,system-ui'; context.fillText(String(hour).padStart(2,'0')+':00',cx,cy+5);
        context.fillStyle=rgba(rgb,.96); context.font='700 8px ui-sans-serif,system-ui'; context.fillText('UTC',cx,cy+19);
      } else {
        context.fillStyle=rgba(rgb,.82); context.font='750 10px ui-sans-serif,system-ui'; context.textAlign='center'; context.textBaseline='top'; context.fillText(month.label.split(' ')[0],cx,box.y+1); context.textBaseline='alphabetic';
      }
      return {day,release,pin};
    }
    function focusLayout(width,height) {
      // The title and colour key occupy protected bands above and below the
      // visual field, so circles and text never compete for the same pixels.
      const stage={x:16,y:76,w:width-32,h:Math.max(170,height-122)};
      // Deliberately reserve the middle of the canvas for one large field.
      // The other eleven months orbit it as small, dim previews.
      const focusSize=Math.min(stage.h*.68,stage.w*.55);
      const focusBox={x:stage.x+stage.w/2-focusSize/2,y:stage.y+stage.h/2-focusSize/2,w:focusSize,h:focusSize};
      const smallSize=Math.min(stage.h*.15,stage.w*.105);
      const radiusX=(stage.w-smallSize)*.485, radiusY=(stage.h-smallSize)*.49;
      const others=MONTHS.map((_,index)=>index).filter(index=>index!==selectedMonth);
      const boxes=new Map([[selectedMonth,focusBox]]);
      others.forEach((monthIndex,slot)=>{
        const angle=-Math.PI/2+Math.PI*2*slot/others.length;
        boxes.set(monthIndex,{x:stage.x+stage.w/2+radiusX*Math.cos(angle)-smallSize/2,y:stage.y+stage.h/2+radiusY*Math.sin(angle)-smallSize/2,w:smallSize,h:smallSize});
      });
      return boxes;
    }
    function draw(progress) {
      const width=bounds.width,height=bounds.height, boxes=focusLayout(width,height);
      context.clearRect(0,0,width,height); context.fillStyle='#040b12'; context.fillRect(0,0,width,height);
      hitAreas=[];
      for(let index=0;index<MONTHS.length;index++) {
        if(index===selectedMonth) continue;
        const box=boxes.get(index); drawTile(index,progress,box,false);
        hitAreas.push({monthIndex:index,cx:box.x+box.w/2,cy:box.y+box.h/2,radius:box.w*.58});
      }
      const focusBox=boxes.get(selectedMonth);
      drawTile(selectedMonth,progress,focusBox,true);
      hitAreas.push({monthIndex:selectedMonth,cx:focusBox.x+focusBox.w/2,cy:focusBox.y+focusBox.h/2,radius:focusBox.w*.54});
      const month=MONTHS[selectedMonth], focusPosition=selectedDate===null ? progress*month.days.length : selectedDate+progress;
      const focusDay=month.days[Math.min(Math.floor(focusPosition),month.days.length-1)], hour=Math.min(24,Math.round((selectedDate===null ? focusPosition-Math.floor(focusPosition) : progress)*24));
      focusLabel.textContent=month.label+' · '+(selectedDate===null?'LIVE MONTH LOOP':label(focusDay.date));
      clockLabel.textContent=String(hour).padStart(2,'0')+':00 UTC · MEAN '+focusDay.mean.toFixed(2)+' M · RANGE '+focusDay.range.toFixed(2)+' M';
    }
    function render(now) {
      const progress=running?cycleAt(now):frozenProgress, key=Math.floor(progress*STEPS);
      if(key!==lastKey) { draw((key+1)/STEPS); lastKey=key; }
      requestAnimationFrame(render);
    }
    canvas.addEventListener('pointerdown',event=>{
      const rect=canvas.getBoundingClientRect(), x=event.clientX-rect.left, y=event.clientY-rect.top;
      const target=hitAreas.map(area=>({...area,distance:Math.hypot(x-area.cx,y-area.cy)})).filter(area=>area.distance<area.radius).sort((first,second)=>first.distance-second.distance)[0];
      if(target && target.monthIndex!==selectedMonth) chooseMonth(target.monthIndex);
    });
    requestAnimationFrame(render);
  </script>
</body>
</html>
"""


def compact_data():
    """Embed the NOAA fields required by the browser, month by month."""
    months = []
    for index, (year, month) in enumerate(WINDOW):
        with monthly_file(year, month).open(encoding="utf-8") as handle:
            reply = json.load(handle)
        days = {}
        for row in reply["data"]:
            date, clock = row["t"].split(" ")
            minutes = int(clock[:2]) * 60 + int(clock[3:])
            days.setdefault(date, []).append(
                [minutes, float(row["v"]), float(row["s"]) if row["s"] else None, row["f"], row["q"]]
            )
        months.append(
            {
                "label": f"{MONTH_NAMES[index]} {year}",
                "days": [{"date": date, "rows": rows} for date, rows in days.items()],
            }
        )
    return json.dumps({"months": months}, separators=(",", ":"))


def main():
    """Write the interactive page and its two annual-output previews."""
    SITE.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    for source in (ANIMATION, STILL):
        shutil.copy2(source, ASSETS / source.name)
    PAGE.write_text(HTML.replace("__DATA__", compact_data()), encoding="utf-8")
    print(f"saved {PAGE.relative_to(HERE)} with twelve cached NOAA month loops")


if __name__ == "__main__":
    main()
