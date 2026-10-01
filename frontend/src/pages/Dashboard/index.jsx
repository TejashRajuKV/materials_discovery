import { Link } from 'react-router-dom';
import Histogram from '../../components/charts/Histogram.jsx';
import { ErrorMessage, Spinner } from '../../components/common/Feedback.jsx';
import { useAsync } from '../../hooks/useAsync.js';
import { getMaterialStats } from '../../services/materialService.js';
import { fmt } from '../../utils/format.js';

export default function Dashboard() {
  const { data, error, loading } = useAsync(() => getMaterialStats());
  return (
    <>
      <h1>Dashboard</h1>
      {loading && <Spinner />}
      <ErrorMessage error={error} />
      {data && (
        <>
          <div className="stats">
            <div className="card"><span className="big">{data.count}</span><span className="muted">materials</span></div>
            <div className="card"><span className="big">{fmt(data.mean_band_gap)} eV</span><span className="muted">mean band gap</span></div>
            <div className="card"><span className="big">{fmt(data.fraction_zero_gap * 100, 0)}%</span><span className="muted">zero gap (metallic)</span></div>
          </div>
          <section><h2>Band gap distribution</h2><Histogram bins={data.histogram} /></section>
          {data.count === 0 && <p className="muted">The database is empty. Run <code>npm run setup</code>.</p>}
        </>
      )}
      <section>
        <h2>Start here</h2>
        <ul>
          <li><Link to="/discovery">Discovery</Link> — describe the band gap you need and rank candidate materials.</li>
          <li><Link to="/predict">Predict</Link> — estimate the band gap of any composition.</li>
          <li><Link to="/materials">Materials</Link> — browse and filter the dataset.</li>
        </ul>
      </section>
    </>
  );
}
