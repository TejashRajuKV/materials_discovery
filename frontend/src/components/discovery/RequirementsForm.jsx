import { useState } from 'react';
import { parseElements, parseList } from '../../utils/format.js';
import ElementPicker from './ElementPicker.jsx';

const initial = {
  min: '1.0', max: '3.0', target: '2.0', maxUncertainty: '0.5', maxEhull: '', include: '', exclude: '', maxElements: '3',
  dimensionality: '', crystalSystem: '',
  feMin: '', feMax: '', bmMin: '', bmMax: '',
  wGap: '', wUnc: '',
};

/** The discovery spec the backend expects, built from the form fields. */
export const buildSpec = (f) => ({
  band_gap: { min: f.min, max: f.max, target: f.target },
  max_uncertainty: f.maxUncertainty,
  include_elements: parseElements(f.include),
  exclude_elements: parseElements(f.exclude),
  max_elements: f.maxElements,
  max_ehull: f.maxEhull,
  dimensionality: parseList(f.dimensionality),
  crystal_system: parseList(f.crystalSystem),
  formation_energy: { min: f.feMin, max: f.feMax },
  bulk_modulus: { min: f.bmMin, max: f.bmMax },
  // Blank means the default ranking weights; otherwise the two weights are normalised by the engine.
  weights: f.wGap === '' && f.wUnc === '' ? undefined : { gap_distance: f.wGap || 0, uncertainty: f.wUnc || 0 },
});

export default function RequirementsForm({ onSubmit, onSave, busy }) {
  const [f, setF] = useState(initial);
  const [saveName, setSaveName] = useState('');
  const set = (key) => (e) => setF((s) => ({ ...s, [key]: e.target.value }));

  const submit = (e) => {
    e.preventDefault();
    onSubmit(buildSpec(f));
  };

  const num = (label, key, hint, step = '0.1') => (
    <label>{label}
      <input type="number" step={step} min="0" value={f[key]} onChange={set(key)} />
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
        <legend>Other properties (predicted for generated candidates)</legend>
        <div className="row">
          {num('Formation energy min (eV/atom)', 'feMin', undefined, 'any')}
          {num('Formation energy max (eV/atom)', 'feMax', 'negative = stable against elements', 'any')}
        </div>
        <div className="row">
          {num('Bulk modulus min (GPa)', 'bmMin', undefined, 'any')}
          {num('Bulk modulus max (GPa)', 'bmMax', undefined, 'any')}
        </div>
      </fieldset>
      <fieldset>
        <legend>Constraints</legend>
        <div className="row">
          {num('Max prediction uncertainty (eV)', 'maxUncertainty')}
          {num('Max energy above hull (eV/atom)', 'maxEhull',
            'stability; blank = no limit. Generated candidates have no stability data, so they are excluded when set', '0.005')}
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
        <ElementPicker
          include={parseElements(f.include)}
          exclude={parseElements(f.exclude)}
          onChange={({ include, exclude }) => setF((s) => ({ ...s, include: include.join(', '), exclude: exclude.join(', ') }))}
        />
        <div className="row">
          <label>Dimensionality
            <input value={f.dimensionality} onChange={set('dimensionality')} placeholder="e.g. 3D-bulk, 2D-bulk" />
            <small className="muted">known materials only; blank = any</small>
          </label>
          <label>Crystal system
            <input value={f.crystalSystem} onChange={set('crystalSystem')} placeholder="e.g. cubic, hexagonal" />
            <small className="muted">known materials only; blank = any</small>
          </label>
        </div>
      </fieldset>
      <fieldset>
        <legend>Ranking weights (optional)</legend>
        <div className="row">
          {num('Weight: distance to target', 'wGap', 'how much closeness to the target matters', 'any')}
          {num('Weight: prediction uncertainty', 'wUnc', 'how much model certainty matters', 'any')}
        </div>
      </fieldset>
      <button type="submit" disabled={busy}>{busy ? 'Starting…' : 'Start discovery'}</button>
      {onSave && (
        <div className="row">
          <label>Save this requirement set as
            <input value={saveName} onChange={(e) => setSaveName(e.target.value)} placeholder="e.g. wide-gap oxides" maxLength={80} />
          </label>
          <button type="button" disabled={busy || !saveName.trim()} onClick={() => { onSave(saveName.trim(), buildSpec(f)); setSaveName(''); }}>
            Save search
          </button>
        </div>
      )}
    </form>
  );
}
