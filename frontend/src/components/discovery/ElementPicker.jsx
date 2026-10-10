import { LANTHANIDES, ACTINIDES, PERIODIC_ROWS } from '../../utils/elements.js';

/**
 * Clickable periodic table. Each click cycles an element: off -> must include -> must exclude -> off.
 * `include` and `exclude` are arrays of symbols; `onChange({ include, exclude })` receives the new lists.
 */
export default function ElementPicker({ include, exclude, onChange }) {
  const state = (symbol) => (include.includes(symbol) ? 'include' : exclude.includes(symbol) ? 'exclude' : 'off');

  const cycle = (symbol) => {
    const next = { off: 'include', include: 'exclude', exclude: 'off' }[state(symbol)];
    const inc = include.filter((s) => s !== symbol);
    const exc = exclude.filter((s) => s !== symbol);
    onChange({
      include: next === 'include' ? [...inc, symbol] : inc,
      exclude: next === 'exclude' ? [...exc, symbol] : exc,
    });
  };

  const cell = (symbol, key) => (symbol ? (
    <button
      type="button"
      key={key}
      className={`element element-${state(symbol)}`}
      aria-label={`${symbol}: ${state(symbol)}`}
      onClick={() => cycle(symbol)}
    >
      {symbol}
    </button>
  ) : <span key={key} className="element element-empty" aria-hidden="true" />);

  return (
    <div className="element-picker">
      <div className="element-grid">
        {PERIODIC_ROWS.map((cells, r) => cells.map((symbol, c) => cell(symbol, `${r}-${c}`)))}
      </div>
      <div className="element-grid element-grid-f">
        {LANTHANIDES.map((s) => cell(s, `la-${s}`))}
      </div>
      <div className="element-grid element-grid-f">
        {ACTINIDES.map((s) => cell(s, `ac-${s}`))}
      </div>
      <p className="muted small">Click an element to require it (green), click again to exclude it (red), again to clear.</p>
    </div>
  );
}
