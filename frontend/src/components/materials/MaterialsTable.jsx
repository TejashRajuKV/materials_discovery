import { Link } from 'react-router-dom';
import { fmt, prettyFormula } from '../../utils/format.js';

export default function MaterialsTable({ items }) {
  if (!items.length) return <p className="muted">No materials match.</p>;
  return (
    <table>
      <thead><tr><th>Formula</th><th>Band gap (eV)</th><th>Predicted (eV)</th><th>± Uncertainty</th><th>Source</th></tr></thead>
      <tbody>
        {items.map((m) => (
          <tr key={m.id}>
            <td><Link to={`/materials/${m.id}`}>{prettyFormula(m.formula)}</Link></td>
            <td>{fmt(m.band_gap)}</td>
            <td>{fmt(m.predicted_band_gap)}</td>
            <td>{fmt(m.uncertainty)}</td>
            <td className="muted">{m.source}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
