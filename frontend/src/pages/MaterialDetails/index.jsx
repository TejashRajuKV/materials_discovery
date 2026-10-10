import { Link, useParams } from 'react-router-dom';
import { ErrorMessage, Spinner } from '../../components/common/Feedback.jsx';
import { useAsync } from '../../hooks/useAsync.js';
import { getMaterial } from '../../services/materialService.js';
import { explain } from '../../services/predictionService.js';
import { fmt, prettyFormula } from '../../utils/format.js';

const PROPERTY_LABELS = {
  formation_energy: 'Formation energy',
  bulk_modulus: 'Bulk modulus',
};

export default function MaterialDetails() {
  const { id } = useParams();
  const material = useAsync(() => getMaterial(id), [id]);
  const info = useAsync(async () => (material.data ? explain(material.data.formula) : null), [material.data?.formula]);
  const m = material.data;
  return (
    <>
      <p><Link to="/materials">← Materials</Link></p>
      <Spinner label={material.loading ? 'Loading…' : ''} />
      <ErrorMessage error={material.error} />
      {m && (
        <>
          <h1>{prettyFormula(m.formula)}</h1>
          <dl className="props">
            <dt>Recorded band gap</dt><dd>{fmt(m.band_gap)} eV</dd>
            <dt>Model prediction</dt><dd>{fmt(m.predicted_band_gap)} ± {fmt(m.uncertainty)} eV</dd>
            <dt>Source</dt><dd>{m.source}</dd>
          </dl>
          {m.properties?.length > 0 && (
            <>
              <h2>Other properties</h2>
              <table className="table">
                <thead><tr><th>Property</th><th>Recorded</th><th>Predicted</th><th>90% interval</th></tr></thead>
                <tbody>
                  {m.properties.map((p) => (
                    <tr key={p.property}>
                      <td>{PROPERTY_LABELS[p.property] ?? p.property}</td>
                      <td>{p.recorded == null ? '—' : `${fmt(p.recorded, 3)} ${p.unit}`}</td>
                      <td>{fmt(p.predicted, 3)} ± {fmt(p.uncertainty, 3)} {p.unit}</td>
                      <td>{fmt(p.interval_low, 3)} – {fmt(p.interval_high, 3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          <h2>What the model sees</h2>
          <ErrorMessage error={info.error} />
          {info.data && (
            <>
              <ul>{info.data.top_features.map((f) => <li key={f.feature}><code>{f.feature}</code> = {fmt(f.value, 3)} (z = {f.z_score})</li>)}</ul>
              <p className="muted small">{info.data.disclaimer}</p>
            </>
          )}
        </>
      )}
    </>
  );
}
