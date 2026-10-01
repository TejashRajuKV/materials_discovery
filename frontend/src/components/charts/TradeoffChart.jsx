/** Scatter of the two objectives (distance to target vs. uncertainty); Pareto front highlighted. */
export default function TradeoffChart({ candidates, onSelect, selectedId, width = 520, height = 260 }) {
  if (!candidates?.length) return null;
  const pad = { l: 44, r: 12, t: 10, b: 36 };
  const xs = candidates.map((c) => c.objectives?.gap_distance ?? Math.abs(c.prediction));
  const maxX = Math.max(...xs, 0.01);
  const maxY = Math.max(...candidates.map((c) => c.uncertainty), 0.01);
  const sx = (v) => pad.l + ((width - pad.l - pad.r) * v) / maxX;
  const sy = (v) => height - pad.b - ((height - pad.t - pad.b) * v) / maxY;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Trade-off between distance to target and uncertainty" className="chart">
      <line x1={pad.l} y1={height - pad.b} x2={width - pad.r} y2={height - pad.b} className="axis" />
      <line x1={pad.l} y1={pad.t} x2={pad.l} y2={height - pad.b} className="axis" />
      <text x={width / 2} y={height - 6} textAnchor="middle" className="tick">distance to target (eV) →  lower is better</text>
      <text x={12} y={height / 2} transform={`rotate(-90 12 ${height / 2})`} textAnchor="middle" className="tick">uncertainty (eV)</text>
      {candidates.map((c, i) => (
        <circle
          key={c.id ?? c.formula}
          cx={sx(xs[i])}
          cy={sy(c.uncertainty)}
          r={c.id === selectedId ? 7 : 5}
          className={c.pareto_rank === 0 ? 'dot dot-front' : 'dot'}
          onClick={() => onSelect?.(c)}
        >
          <title>{`${c.formula}: ${c.prediction} eV ± ${c.uncertainty}`}</title>
        </circle>
      ))}
    </svg>
  );
}
