import { ConfidenceBadge, Badge } from '../common/Feedback.jsx';
import { fmt, prettyFormula } from '../../utils/format.js';

const VALIDATION_TONE = { pass: 'good', warn: 'warn', fail: 'bad' };

export default function CandidateTable({ candidates, selected, onToggle, onOpen, openId }) {
  if (!candidates.length) return <p className="muted">No candidates satisfied the requirements.</p>;
  return (
    <table>
      <thead>
        <tr><th aria-label="Compare" /><th>#</th><th>Formula</th><th>Band gap (eV)</th><th>± Unc.</th>
          <th>Confidence</th><th>Pareto</th><th>Validation</th></tr>
      </thead>
      <tbody>
        {candidates.map((c) => (
          <tr key={c.id} className={c.id === openId ? 'row-open' : ''}>
            <td><input type="checkbox" aria-label={`Compare ${c.formula}`} checked={selected.includes(c.id)} onChange={() => onToggle(c.id)} /></td>
            <td>{c.rank}</td>
            <td><button className="link" onClick={() => onOpen(c)}>{prettyFormula(c.formula)}</button></td>
            <td>{fmt(c.prediction)}</td>
            <td>{fmt(c.uncertainty)}</td>
            <td><ConfidenceBadge confidence={c.confidence} /></td>
            <td>{c.pareto_rank === 0 ? <Badge tone="good">front</Badge> : <span className="muted">{c.pareto_rank}</span>}</td>
            <td><Badge tone={VALIDATION_TONE[c.validation?.overall] ?? 'neutral'}>{c.validation?.overall ?? '—'}</Badge></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
