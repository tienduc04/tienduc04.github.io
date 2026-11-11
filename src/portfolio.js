// Mean-variance maths for the demo widget. Weights are fractions that sum to 1.
export function stats(w, assets, corr, rf) {
  let ret = 0, variance = 0;
  for (let i = 0; i < assets.length; i++) {
    ret += w[i] * assets[i].ret;
    for (let j = 0; j < assets.length; j++) variance += w[i] * w[j] * assets[i].vol * assets[j].vol * corr[i][j];
  }
  const vol = Math.sqrt(Math.max(variance, 0));
  return { ret, vol, sharpe: vol > 1e-9 ? (ret - rf) / vol : 0 };
}

// Long-only efficient frontier: try every weight mix on a grid, keep the best return per volatility bucket.
export function frontier(assets, corr, rf, step = 0.05, buckets = 40) {
  const n = assets.length, steps = Math.round(1 / step), pts = [];
  const walk = (i, left, w) => {
    if (i === n - 1) return pts.push(stats([...w, left * step], assets, corr, rf));
    for (let k = 0; k <= left; k++) walk(i + 1, left - k, [...w, k * step]);
  };
  walk(0, steps, []);
  const maxVol = Math.max(...pts.map((p) => p.vol));
  const best = new Array(buckets).fill(null);
  for (const p of pts) {
    const b = Math.min(buckets - 1, Math.floor((p.vol / maxVol) * buckets));
    if (!best[b] || p.ret > best[b].ret) best[b] = p;
  }
  // Keep only the upper-left edge: each point must beat the return of every lower-risk point.
  const out = [];
  for (const p of best.filter(Boolean)) if (!out.length || p.ret > out[out.length - 1].ret) out.push(p);
  return out;
}

export const normalise = (raw) => {
  const sum = raw.reduce((a, b) => a + b, 0);
  return sum > 0 ? raw.map((x) => x / sum) : raw.map(() => 0);
};
