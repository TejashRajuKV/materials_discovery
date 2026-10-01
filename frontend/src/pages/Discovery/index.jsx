import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import RequirementsForm from '../../components/discovery/RequirementsForm.jsx';
import { ErrorMessage, Badge } from '../../components/common/Feedback.jsx';
import { useAsync } from '../../hooks/useAsync.js';
import { listJobs, startDiscovery } from '../../services/discoveryService.js';

export default function Discovery() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const jobs = useAsync(() => listJobs());

  const submit = async (spec) => {
    setBusy(true); setError(null);
    try {
      const job = await startDiscovery(spec);
      navigate(`/discovery/${job.id}`);
    } catch (err) {
      setError(err); setBusy(false);
    }
  };

  return (
    <>
      <h1>Discovery</h1>
      <p className="muted">Describe the material you need. The engine screens known materials and chemically-motivated substitution candidates, predicts their band gap, validates them, and ranks the trade-offs.</p>
      <RequirementsForm onSubmit={submit} busy={busy} />
      <ErrorMessage error={error} />
      {jobs.data?.length > 0 && (
        <section>
          <h2>Previous jobs</h2>
          <ul>{jobs.data.map((j) => (
            <li key={j.id}><Link to={`/discovery/${j.id}`}>Job #{j.id}</Link>{' '}
              <Badge tone={j.status === 'completed' ? 'good' : j.status === 'failed' ? 'bad' : 'warn'}>{j.status}</Badge>{' '}
              <span className="muted">{j.created_at}</span></li>
          ))}</ul>
        </section>
      )}
    </>
  );
}
