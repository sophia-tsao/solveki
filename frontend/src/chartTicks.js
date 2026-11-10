// Clean whole-number axis ticks from 0 up past `max`: a 1/2/5 step giving
// about 4 intervals.
export function niceTicks(max) {
  if (max <= 0) return [0, 1];
  const raw = Math.max(1, max / 4);
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * mag).find((s) => s >= raw);
  const ticks = [];
  for (let t = 0; t < max + step; t += step) ticks.push(t);
  return ticks;
}
