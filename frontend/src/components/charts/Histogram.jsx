/** Simple SVG bar chart: bins = [{bin_start, count}]. */
export default function Histogram({ bins, width = 520, height = 180, label = 'Band gap (eV)' }) {
  if (!bins?.length) return null;
  const pad = { l: 36, r: 8, t: 8, b: 28 };
  const max = Math.max(...bins.map((b) => b.count));
  const bw = (width - pad.l - pad.r) / bins.length;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Histogram of ${label}`} className="chart">
      {bins.map((b, i) => {
        const h = ((height - pad.t - pad.b) * b.count) / max;
        return (
          <g key={b.bin_start}>
            <rect x={pad.l + i * bw + 1} y={height - pad.b - h} width={bw - 2} height={h} className="bar">
              <title>{`${b.bin_start}–${b.bin_start + 0.5} eV: ${b.count}`}</title>
            </rect>
            {i % 2 === 0 && <text x={pad.l + i * bw + bw / 2} y={height - 10} textAnchor="middle" className="tick">{b.bin_start}</text>}
          </g>
        );
      })}
      <text x={pad.l - 6} y={pad.t + 8} textAnchor="end" className="tick">{max}</text>
      <text x={width / 2} y={height} textAnchor="middle" className="tick">{label}</text>
    </svg>
  );
}
