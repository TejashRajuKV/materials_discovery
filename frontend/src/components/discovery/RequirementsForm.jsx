import { useState } from 'react';
import { parseElements } from '../../utils/format.js';

const initial = { min: '1.0', max: '3.0', target: '2.0', maxUncertainty: '0.5', include: '', exclude: '', maxElements: '3' };

export default function RequirementsForm({ onSubmit, busy }) {
  const [f, setF] = useState(initial);
  const set = (key) => (e) => setF((s) => ({ ...s, [key]: e.target.value }));

  const submit = (e) => {
    e.preventDefault();
    onSubmit({
      band_gap: { min: f.min, max: f.max, target: f.target },
      max_uncertainty: f.maxUncertainty,
      include_elements: parseElements(f.include),
      exclude_elements: parseElements(f.exclude),
      max_elements: f.maxElements,
    });
  };

  const num = (label, key, hint) => (
    <label>{label}
      <input type="number" step="0.1" min="0" value={f[key]} onChange={set(key)} />
      {hint && <small className="muted">{hint}</small>}
    </label>
  );

  return (
    <form onSubmit={submit} className="form">
      <fieldset>
        <legend>Band gap requirement (eV)</legend>
        <div className="row">
          {num('Minimum', 'min')}
          {num('Maximum', 'max')}
          {num('Target', 'target', 'ranking prefers values near this')}
        </div>
      </fieldset>
      <fieldset>
        <legend>Constraints</legend>
        <div className="row">
          {num('Max prediction uncertainty (eV)', 'maxUncertainty')}
          <label>Max number of elements
            <input type="number" min="1" max="6" value={f.maxElements} onChange={set('maxElements')} />
          </label>
        </div>
        <div className="row">
          <label>Must include elements
            <input value={f.include} onChange={set('include')} placeholder="e.g. O, Ti" />
          </label>
          <label>Exclude elements
            <input value={f.exclude} onChange={set('exclude')} placeholder="e.g. Pb, Cd" />
          </label>
        </div>
      </fieldset>
      <button type="submit" disabled={busy}>{busy ? 'Starting…' : 'Start discovery'}</button>
    </form>
  );
}
