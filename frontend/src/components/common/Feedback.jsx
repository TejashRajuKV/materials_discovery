export function Spinner({ label = 'Loading…' }) {
  return <p className="muted" role="status">{label}</p>;
}

export function ErrorMessage({ error }) {
  if (!error) return null;
  return <p className="error" role="alert">{error.message || String(error)}</p>;
}

export function Badge({ tone = 'neutral', children }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

const CONFIDENCE_TONE = { high: 'good', recorded: 'good', medium: 'warn', low: 'bad' };
export const ConfidenceBadge = ({ confidence }) => <Badge tone={CONFIDENCE_TONE[confidence] ?? 'neutral'}>{confidence}</Badge>;
