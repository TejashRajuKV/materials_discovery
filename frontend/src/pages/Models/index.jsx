import { ErrorMessage, Spinner } from '../../components/common/Feedback.jsx';
import { useAsync } from '../../hooks/useAsync.js';
import { listModels } from '../../services/predictionService.js';
import { fmt } from '../../utils/format.js';

export default function Models() {
  const { data, error, loading } = useAsync(() => listModels());
  const model = data?.[0];
  return (
    <>
      <h1>Models</h1>
      {loading && <Spinner />}
      <ErrorMessage error={error} />
      {data && !model && <p className="muted">No model registered. Run <code>npm run setup</code>.</p>}
      {model && (
        <>
          <p>Active: <strong>{model.algorithm}</strong> · target <code>{model.target_property}</code> · version {model.version}</p>
          <p className="muted small">
            Split: {model.details.split}. Train {model.details.n_train} / test {model.details.n_test}. Data: {model.details.data_source.join(', ')}.
          </p>
          <h2>Held-out performance</h2>
          <table>
            <thead><tr><th>Model</th><th>CV MAE</th><th>Test MAE</th><th>Test RMSE</th><th>Test R²</th></tr></thead>
            <tbody>{Object.entries(model.metrics).map(([name, r]) => (
              <tr key={name}><td>{name}</td><td>{fmt(r.cv.mae, 3)}</td><td>{fmt(r.test.mae, 3)}</td><td>{fmt(r.test.rmse, 3)}</td><td>{fmt(r.test.r2, 3)}</td></tr>
            ))}</tbody>
          </table>
          <h2>Error by band-gap range (test set)</h2>
          <table>
            <thead><tr><th>Range (eV)</th><th>n</th><th>MAE</th></tr></thead>
            <tbody>{Object.entries(model.details.error_analysis.by_gap_range).map(([k, r]) => <tr key={k}><td>{k}</td><td>{r.n}</td><td>{fmt(r.mae, 3)}</td></tr>)}</tbody>
          </table>
          <h2>Top features (random forest importance)</h2>
          <ul>{Object.entries(model.details.feature_importance).slice(0, 8).map(([k, v]) => <li key={k}><code>{k}</code> — {fmt(v, 3)}</li>)}</ul>
          <p className="muted small">Uncertainty/|error| correlation on held-out data: {fmt(model.details.uncertainty.std_vs_abs_error_corr)}.</p>
        </>
      )}
    </>
  );
}
