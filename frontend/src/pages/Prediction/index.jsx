import { useState } from 'react';
import PredictionCard from '../../components/predictions/PredictionCard.jsx';
import { ErrorMessage } from '../../components/common/Feedback.jsx';
import { predict } from '../../services/predictionService.js';
import { parseElements } from '../../utils/format.js';

export const PROPERTIES = [
  { value: 'band_gap', label: 'Band gap (eV)' },
  { value: 'formation_energy', label: 'Formation energy (eV/atom)' },
  { value: 'bulk_modulus', label: 'Bulk modulus (GPa)' },
];

export default function Prediction() {
  const [text, setText] = useState('MgO, TiO2, ZnS');
  const [property, setProperty] = useState('band_gap');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      setResults((await predict(parseElements(text), property)).predictions);
    } catch (err) {
      setError(err); setResults(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <h1>Property prediction</h1>
      <p className="muted">Enter chemical formulas (comma or space separated). Each prediction has a 90% interval. Band-gap intervals are calibrated on chemistry the model had not seen, so they are wide for large predicted gaps; formation-energy and bulk-modulus intervals are calibrated on JARVIS held-out data and are narrower. The ± value is the model's per-material spread.</p>
      <form onSubmit={submit} className="form">
        <label>Formulas<input value={text} onChange={(e) => setText(e.target.value)} placeholder="LiFePO4, GaN" /></label>
        <label>Property
          <select value={property} onChange={(e) => setProperty(e.target.value)}>
            {PROPERTIES.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </label>
        <button type="submit" disabled={busy || !text.trim()}>{busy ? 'Predicting…' : 'Predict'}</button>
      </form>
      <ErrorMessage error={error} />
      {results && <div className="cards">{results.map((r, i) => <PredictionCard key={`${r.input}-${i}`} result={r} />)}</div>}
    </>
  );
}
