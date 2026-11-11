import { stats, frontier, normalise } from './portfolio.js';

const pct = (x, d = 1) => `${(x * 100).toFixed(d)}%`;
const NS = 'http://www.w3.org/2000/svg';
const el = (tag, attrs = {}, parent) => {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  parent?.appendChild(e);
  return e;
};

export function initDemo(root, { assets, corr, riskFree }) {
  root.innerHTML = `
    <div>
      <h3>Weights</h3>
      <div class="sliders"></div>
      <button type="button" class="reset">Reset weights</button>
    </div>
    <div>
      <h3 class="sr-only">Results</h3>
      <svg class="chart" viewBox="0 0 520 320" role="img" aria-label="Risk–return chart: volatility on the horizontal axis, expected return on the vertical axis, with the efficient frontier and your portfolio"></svg>
      <ul class="stats" aria-live="polite">
        <li><strong data-k="ret"></strong><span>Expected return</span></li>
        <li><strong data-k="vol"></strong><span>Volatility</span></li>
        <li><strong data-k="sharpe"></strong><span>Sharpe ratio (rf ${pct(riskFree)})</span></li>
      </ul>
    </div>`;

  const raw = assets.map((a) => a.weight);
  const box = root.querySelector('.sliders');
  const inputs = assets.map((a, i) => {
    const row = document.createElement('div');
    row.className = 'slider';
    row.innerHTML = `<label for="w${i}">${a.name}</label><output id="o${i}" for="w${i}"></output>
      <input id="w${i}" type="range" min="0" max="100" step="1" value="${a.weight}" aria-describedby="o${i}">`;
    box.appendChild(row);
    const input = row.querySelector('input');
    input.addEventListener('input', () => { raw[i] = +input.value; update(); });
    return input;
  });
  root.querySelector('.reset').addEventListener('click', () => {
    assets.forEach((a, i) => { raw[i] = a.weight; inputs[i].value = a.weight; });
    update();
  });

  // Chart scales
  const svg = root.querySelector('.chart');
  const pad = { l: 52, r: 16, t: 16, b: 40 }, W = 520, H = 320;
  const maxVol = Math.max(...assets.map((a) => a.vol)) * 1.15;
  const rets = assets.map((a) => a.ret);
  const minRet = Math.min(...rets) - 0.01, maxRet = Math.max(...rets) + 0.01;
  const x = (v) => pad.l + (v / maxVol) * (W - pad.l - pad.r);
  const y = (r) => H - pad.b - ((r - minRet) / (maxRet - minRet)) * (H - pad.t - pad.b);

  el('line', { class: 'axis', x1: pad.l, y1: H - pad.b, x2: W - pad.r, y2: H - pad.b }, svg);
  el('line', { class: 'axis', x1: pad.l, y1: pad.t, x2: pad.l, y2: H - pad.b }, svg);
  for (let v = 0; v <= maxVol; v += 0.05) el('text', { x: x(v), y: H - pad.b + 18, 'text-anchor': 'middle' }, svg).textContent = pct(v, 0);
  const yStep = maxRet - minRet > 0.08 ? 0.02 : 0.01;
  for (let r = Math.ceil(minRet / yStep) * yStep; r <= maxRet; r += yStep) el('text', { x: pad.l - 8, y: y(r) + 4, 'text-anchor': 'end' }, svg).textContent = pct(r, 0);
  el('text', { x: (W + pad.l) / 2, y: H - 4, 'text-anchor': 'middle' }, svg).textContent = 'Volatility (risk)';
  el('text', { x: 14, y: (H - pad.b) / 2, 'text-anchor': 'middle', transform: `rotate(-90 14 ${(H - pad.b) / 2})` }, svg).textContent = 'Expected return';

  const f = frontier(assets, corr, riskFree);
  el('polyline', { class: 'frontier', points: f.map((p) => `${x(p.vol)},${y(p.ret)}`).join(' ') }, svg);
  assets.forEach((a) => {
    el('circle', { class: 'asset', cx: x(a.vol), cy: y(a.ret), r: 5 }, svg);
    el('text', { x: x(a.vol) + 8, y: y(a.ret) + 4 }, svg).textContent = a.name.match(/\((\w+)\)/)?.[1] ?? a.name; // ticker keeps the chart uncluttered
  });
  const you = el('circle', { class: 'you', r: 8 }, svg);
  const youLabel = el('text', {}, svg);
  youLabel.textContent = 'Your mix';

  const out = { ret: root.querySelector('[data-k=ret]'), vol: root.querySelector('[data-k=vol]'), sharpe: root.querySelector('[data-k=sharpe]') };
  function update() {
    const w = normalise(raw);
    w.forEach((v, i) => (root.querySelector(`#o${i}`).textContent = pct(v, 0)));
    if (w.every((v) => v === 0)) {
      out.ret.textContent = out.vol.textContent = out.sharpe.textContent = '–';
      you.setAttribute('visibility', 'hidden');
      youLabel.setAttribute('visibility', 'hidden');
      return;
    }
    const s = stats(w, assets, corr, riskFree);
    out.ret.textContent = pct(s.ret);
    out.vol.textContent = pct(s.vol);
    out.sharpe.textContent = s.sharpe.toFixed(2);
    you.setAttribute('visibility', 'visible');
    youLabel.setAttribute('visibility', 'visible');
    you.setAttribute('cx', x(s.vol));
    you.setAttribute('cy', y(s.ret));
    youLabel.setAttribute('x', x(s.vol) + 12);
    youLabel.setAttribute('y', y(s.ret) - 10);
  }
  update();
}
