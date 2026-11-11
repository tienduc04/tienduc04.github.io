import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { stats, frontier, normalise } from './portfolio.js';

const { assets, corr, riskFree } = JSON.parse(readFileSync(new URL('../content/site.json', import.meta.url))).demo;
const w = (...first) => assets.map((_, i) => first[i] ?? 0); // pads weights to the number of assets
const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);

test('single asset portfolio has that asset’s return and volatility', () => {
  const s = stats(w(1), assets, corr, riskFree);
  close(s.ret, assets[0].ret);
  close(s.vol, assets[0].vol);
  close(s.sharpe, (assets[0].ret - riskFree) / assets[0].vol);
});

test('two-asset volatility matches the textbook formula', () => {
  const [a, b] = assets, r = corr[0][1];
  const expected = Math.sqrt(0.25 * a.vol ** 2 + 0.25 * b.vol ** 2 + 2 * 0.25 * a.vol * b.vol * r);
  close(stats(w(0.5, 0.5), assets, corr, riskFree).vol, expected);
});

test('diversification lowers risk below the weighted average', () => {
  const s = stats(w(0.5, 0.5), assets, corr, riskFree);
  assert.ok(s.vol < 0.5 * assets[0].vol + 0.5 * assets[1].vol);
});

test('frontier rises with risk and normalise handles zero', () => {
  const f = frontier(assets, corr, riskFree);
  assert.ok(f.length > 5);
  for (let i = 1; i < f.length; i++) assert.ok(f[i].ret > f[i - 1].ret && f[i].vol >= f[i - 1].vol);
  assert.deepEqual(normalise([0, 0, 0, 0]), [0, 0, 0, 0]);
  close(normalise([1, 1, 2, 0]).reduce((a, b) => a + b), 1);
});
