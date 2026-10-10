import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import RequirementsForm from '../../components/discovery/RequirementsForm.jsx';
import { ErrorMessage, Badge } from '../../components/common/Feedback.jsx';
import { useAsync } from '../../hooks/useAsync.js';
import { listJobs, startDiscovery } from '../../services/discoveryService.js';
import { deleteSearch, listSearches, runSearch, saveSearch } from '../../services/searchService.js';

export default function Discovery() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const jobs = useAsync(() => listJobs());
  const searches = useAsync(() => listSearches(), []);

  const submit = async (spec) => {
    setBusy(true); setError(null);
    try {
      const job = await startDiscovery(spec);
      navigate(`/discovery/${job.id}`);
    } catch (err) {
      setError(err); setBusy(false);
    }
  };

  const save = async (name, spec) => {
    setError(null);
    try {
      await saveSearch(name, spec);
      searches.reload();
    } catch (err) {
      setError(err);
    }
  };

  const run = async (id) => {
    setError(null);
    try {
      const job = await runSearch(id);
      navigate(`/discovery/${job.id}`);
    } catch (err) {
      setError(err);
    }
  };

  const remove = async (id) => {
    await deleteSearch(id);
    searches.reload();
  };

  return (
    <>
      <h1>Discovery</h1>
      <p className="muted">Describe the material you need. The engine screens known materials and chemically-motivated substitution candidates, predicts their band gap, validates them, and ranks the trade-offs.</p>
      <RequirementsForm onSubmit={submit} onSave={save} busy={busy} />
      <ErrorMessage error={error} />
      {searches.data?.length > 0 && (
        <section>
          <h2>Saved searches</h2>
          <ul>{searches.data.map((x) => (
            <li key={x.id}>
              <strong>{x.name}</strong>{' '}
              <button type="button" onClick={() => run(x.id)}>Run</button>{' '}
              <button type="button" onClick={() => remove(x.id)}>Delete</button>{' '}
              <span className="muted">saved {x.created_at}</span>
            </li>
          ))}</ul>
        </section>
      )}
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
