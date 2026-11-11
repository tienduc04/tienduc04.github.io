// Shared by the 3D hero and the static SVG fallback so both show the same "price terrain".
export function barHeight(i, j, cols, rows, t = 0) {
  const x = i / cols, z = j / rows;
  const trend = 0.6 + 1.4 * x; // drifts upward left to right, like a rising market
  const swing =
    0.45 * Math.sin(x * 9 + z * 2.5 + t) +
    0.25 * Math.sin(x * 23 - z * 5 + t * 0.7) +
    0.2 * Math.cos(z * 7 + x * 3);
  return Math.max(0.15, trend + swing);
}

// A bar is "up" (copper) when it is higher than its left neighbour, like a green candle.
export const isUp = (i, j, cols, rows, t = 0) =>
  i === 0 || barHeight(i, j, cols, rows, t) >= barHeight(i - 1, j, cols, rows, t);
