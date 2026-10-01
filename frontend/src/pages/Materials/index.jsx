import { useState } from 'react';
import MaterialsTable from '../../components/materials/MaterialsTable.jsx';
import { ErrorMessage, Spinner } from '../../components/common/Feedback.jsx';
import { useAsync } from '../../hooks/useAsync.js';
import { listMaterials } from '../../services/materialService.js';

const PAGE = 25;

export default function Materials() {
  const [filters, setFilters] = useState({ q: '', min_gap: '', max_gap: '', sort: 'formula' });
  const [draft, setDraft] = useState(filters);
  const [page, setPage] = useState(0);
  const { data, error, loading } = useAsync(
    (signal) => listMaterials({ ...filters, limit: PAGE, offset: page * PAGE }, signal),
    [filters, page],
  );
  const bind = (key) => ({ value: draft[key], onChange: (e) => setDraft((d) => ({ ...d, [key]: e.target.value })) });
  const submit = (e) => { e.preventDefault(); setPage(0); setFilters(draft); };
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE)) : 1;

  return (
    <>
      <h1>Materials</h1>
      <form onSubmit={submit} className="form row">
        <label>Formula contains<input {...bind('q')} placeholder="e.g. Mg" /></label>
        <label>Min gap (eV)<input type="number" step="0.1" {...bind('min_gap')} /></label>
        <label>Max gap (eV)<input type="number" step="0.1" {...bind('max_gap')} /></label>
        <label>Sort
          <select {...bind('sort')}>
            <option value="formula">Formula</option>
            <option value="band_gap">Band gap ↑</option>
            <option value="-band_gap">Band gap ↓</option>
          </select>
        </label>
        <button type="submit">Search</button>
      </form>
      {loading && <Spinner />}
      <ErrorMessage error={error} />
      {data && (
        <>
          <p className="muted">{data.total} results</p>
          <MaterialsTable items={data.items} />
          <div className="pager">
            <button disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</button>
            <span>Page {page + 1} of {pages}</span>
            <button disabled={page + 1 >= pages} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </>
      )}
    </>
  );
}
