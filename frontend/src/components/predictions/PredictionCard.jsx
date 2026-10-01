import { ConfidenceBadge } from '../common/Feedback.jsx';
import { fmt, prettyFormula } from '../../utils/format.js';

export default function PredictionCard({ result }) {
  if (result.error) {
    return <div className="card card-error"><strong>{result.input}</strong><p className="error">{result.error}</p></div>;
  }
  return (
    <div className="card">
      <h3>{prettyFormula(result.formula)}</h3>
      <p className="big">{fmt(result.prediction)} <small>eV ± {fmt(result.uncertainty)}</small></p>
      {result.interval && (
        <p className="muted">{Math.round(result.interval_level * 100)}% interval: {fmt(result.interval[0])}–{fmt(result.interval[1])} eV</p>
      )}
      <p><ConfidenceBadge confidence={result.confidence} /> <span className="muted">model: {result.model}</span></p>
      {result.known_band_gap != null && (
        <p className="muted">Recorded in dataset: {fmt(result.known_band_gap)} eV</p>
      )}
    </div>
  );
}
