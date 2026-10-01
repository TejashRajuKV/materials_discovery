import { Link, useSearchParams } from 'react-router-dom';
import { Badge, ConfidenceBadge, ErrorMessage, Spinner } from '../../components/common/Feedback.jsx';
import { useAsync } from '../../hooks/useAsync.js';
import { compareCandidates } from '../../services/discoveryService.js';
import { fmt, prettyFormula } from '../../utils/format.js';

export default function Comparison() {
  const [params] = useSearchParams();
  const ids = (params.get('ids') ?? '').split(',').filter(Boolean);
  const { data, error, loading } = useAsync(() => compareCandidates(ids), [params.toString()]);

  const layerStatus = (c, layer) => c.validation?.layers?.find((l) => l.layer === layer)?.status ?? '—';
  const rows = [
    ['Origin', (c) => c.origin],
    ['Predicted band gap (eV)', (c) => fmt(c.prediction)],
    ['Uncertainty (eV)', (c) => fmt(c.uncertainty)],
    ['Confidence', (c) => <ConfidenceBadge confidence={c.confidence} />],
    ['Pareto rank', (c) => (c.pareto_rank === 0 ? <Badge tone="good">front</Badge> : c.pareto_rank)],
    ['Score', (c) => fmt(c.score, 3)],
    ['Chemical validity', (c) => layerStatus(c, 'chemical')],
    ['Property constraints', (c) => layerStatus(c, 'property_constraints')],
    ['Stability', (c) => layerStatus(c, 'stability').replace('_', ' ')],
  ];
  return (
    <>
      <p><Link to="/discovery">← Discovery</Link></p>
      <h1>Candidate comparison</h1>
      {loading && <Spinner />}
      <ErrorMessage error={error} />
      {data && (
        <table>
          <thead><tr><th />{data.map((c) => <th key={c.id}>{prettyFormula(c.formula)}</th>)}</tr></thead>
          <tbody>{rows.map(([label, f]) => <tr key={label}><th scope="row">{label}</th>{data.map((c) => <td key={c.id}>{f(c)}</td>)}</tr>)}</tbody>
        </table>
      )}
      <p className="muted small">There is no single “best” material — compare trade-offs across the rows.</p>
    </>
  );
}
