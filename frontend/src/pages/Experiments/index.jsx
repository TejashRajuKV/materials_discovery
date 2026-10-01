import { ErrorMessage, Spinner } from '../../components/common/Feedback.jsx';
import { useAsync } from '../../hooks/useAsync.js';
import { listExperiments } from '../../services/predictionService.js';
import { fmt } from '../../utils/format.js';

export default function Experiments() {
  const { data, error, loading } = useAsync(() => listExperiments());
  return (
    <>
      <h1>Experiments</h1>
      {loading && <Spinner />}
      <ErrorMessage error={error} />
      {data?.length === 0 && <p className="muted">No experiments recorded.</p>}
      {data?.map((e) => (
        <section key={e.id} className="card">
          <h2>{e.name} <small className="muted">· model {e.model_version}</small></h2>
          <p className="muted">Dataset: {e.dataset}. {e.notes}</p>
          <table>
            <thead><tr><th>Model</th><th>CV MAE</th><th>Test MAE</th><th>Test R²</th></tr></thead>
            <tbody>{Object.entries(e.metrics).map(([name, r]) => (
              <tr key={name}><td>{name}</td><td>{fmt(r.cv.mae, 3)}</td><td>{fmt(r.test.mae, 3)}</td><td>{fmt(r.test.r2, 3)}</td></tr>
            ))}</tbody>
          </table>
        </section>
      ))}
    </>
  );
}
