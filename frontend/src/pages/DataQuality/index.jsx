import { ErrorMessage, Spinner } from '../../components/common/Feedback.jsx';
import { useAsync } from '../../hooks/useAsync.js';
import { getDataQuality } from '../../services/dataService.js';
import { fmt } from '../../utils/format.js';

const pct = (part, whole) => (whole ? `${fmt((100 * part) / whole, 1)}%` : '—');

export default function DataQuality() {
  const report = useAsync(() => getDataQuality(), []);
  const r = report.data;
  return (
    <>
      <h1>Data quality</h1>
      <p className="muted">What preprocessing dropped and merged from the JARVIS source table, and the shape of the target it kept.</p>
      <Spinner label={report.loading ? 'Loading…' : ''} />
      <ErrorMessage error={report.error} />
      {r && (
        <>
          <dl className="props">
            <dt>Source</dt><dd>{r.source}</dd>
            <dt>Entries in</dt><dd>{r.rows_in.toLocaleString()}</dd>
            <dt>Dropped: unparseable formula</dt><dd>{r.dropped_invalid_formula.toLocaleString()} ({pct(r.dropped_invalid_formula, r.rows_in)})</dd>
            <dt>Dropped: missing or negative target</dt><dd>{r.dropped_missing_or_negative_target.toLocaleString()}</dd>
            <dt>Merged: duplicate formulas (median)</dt><dd>{r.merged_duplicates.toLocaleString()} ({pct(r.merged_duplicates, r.rows_in)})</dd>
            <dt>Training rows</dt><dd>{r.rows_out.toLocaleString()}</dd>
            <dt>Validation</dt><dd>{r.valid ? 'passed' : `failed: ${r.problems.join('; ')}`}</dd>
          </dl>
          <h2>Band-gap target</h2>
          <dl className="props">
            <dt>Mean / std</dt><dd>{fmt(r.target.mean, 3)} / {fmt(r.target.std, 3)} eV</dd>
            <dt>Range</dt><dd>{fmt(r.target.min, 3)} – {fmt(r.target.max, 3)} eV</dd>
            <dt>Exactly zero (metals)</dt><dd>{pct(r.target.fraction_zero_gap * r.target.count, r.target.count)}</dd>
          </dl>
          {r.stability && (
            <>
              <h2>Stability and properties</h2>
              <dl className="props">
                <dt>Formulas with stability</dt><dd>{r.stability.formulas.toLocaleString()}</dd>
                <dt>Within 0.025 eV/atom of the hull</dt><dd>{r.stability["below_0.025_eV_per_atom"].toLocaleString()}</dd>
                {r.property_formation_energy != null && <><dt>Formation energy formulas</dt><dd>{r.property_formation_energy.toLocaleString()}</dd></>}
                {r.property_bulk_modulus != null && <><dt>Bulk modulus formulas</dt><dd>{r.property_bulk_modulus.toLocaleString()}</dd></>}
              </dl>
            </>
          )}
        </>
      )}
    </>
  );
}
