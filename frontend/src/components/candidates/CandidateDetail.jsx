import { Badge } from '../common/Feedback.jsx';
import { fmt, prettyFormula } from '../../utils/format.js';

const TONE = { pass: 'good', warn: 'warn', fail: 'bad', not_assessed: 'neutral' };

export default function CandidateDetail({ candidate }) {
  if (!candidate) return <p className="muted">Select a candidate to see validation and explanation.</p>;
  const { validation, explanation } = candidate;
  return (
    <div className="card">
      <h3>{prettyFormula(candidate.formula)} <small className="muted">({candidate.origin})</small></h3>
      <p>{fmt(candidate.prediction)} eV ± {fmt(candidate.uncertainty)} · score {fmt(candidate.score, 3)}</p>

      <h4>Validation layers</h4>
      <ul className="plain">
        {validation?.layers?.map((l) => (
          <li key={l.layer}>
            <Badge tone={TONE[l.status]}>{l.status.replace('_', ' ')}</Badge> <strong>{l.layer.replace('_', ' ')}</strong>
            <ul>{l.checks.map((c) => <li key={c.name} className="muted">{c.ok === false ? '✗' : c.ok ? '✓' : '·'} {c.name}: {c.detail}</li>)}</ul>
          </li>
        ))}
      </ul>

      {explanation ? (
        <>
          <h4>Why this candidate</h4>
          <p className="muted">Features the model relies on most for this composition:</p>
          <ul>{explanation.top_features.map((f) => (
            <li key={f.feature}><code>{f.feature}</code> = {fmt(f.value, 3)} (z = {f.z_score}, importance {fmt(f.importance, 3)})</li>
          ))}</ul>
          <p className="muted">Most similar known materials:</p>
          <ul>{explanation.similar_known_materials.map((m) => (
            <li key={m.formula}>{prettyFormula(m.formula)} — {fmt(m.band_gap)} eV (distance {m.distance})</li>
          ))}</ul>
          <p className="muted small">{explanation.disclaimer}</p>
        </>
      ) : <p className="muted small">Explanations are generated for the top-ranked candidates only.</p>}
    </div>
  );
}
