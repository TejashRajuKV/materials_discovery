import { useState } from 'react';
import PredictionCard from '../../components/predictions/PredictionCard.jsx';
import { ErrorMessage } from '../../components/common/Feedback.jsx';
import { predict } from '../../services/predictionService.js';
import { parseElements } from '../../utils/format.js';

export default function Prediction() {
  const [text, setText] = useState('MgO, TiO2, ZnS');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      setResults((await predict(parseElements(text))).predictions);
    } catch (err) {
      setError(err); setResults(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <h1>Property prediction</h1>
      <p className="muted">Enter chemical formulas (comma or space separated). Uncertainty is the spread of the random forest's trees — a relative signal, not a calibrated interval.</p>
      <form onSubmit={submit} className="form">
        <label>Formulas<input value={text} onChange={(e) => setText(e.target.value)} placeholder="LiFePO4, GaN" /></label>
        <button type="submit" disabled={busy || !text.trim()}>{busy ? 'Predicting…' : 'Predict band gap'}</button>
      </form>
      <ErrorMessage error={error} />
      {results && <div className="cards">{results.map((r, i) => <PredictionCard key={`${r.input}-${i}`} result={r} />)}</div>}
    </>
  );
}
