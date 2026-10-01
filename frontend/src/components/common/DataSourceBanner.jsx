import { useAsync } from '../../hooks/useAsync.js';
import { listModels } from '../../services/predictionService.js';

/** Loud warning while the active model was trained on the synthetic demo dataset. */
export default function DataSourceBanner() {
  const { data } = useAsync(() => listModels());
  const sources = data?.[0]?.details?.data_source ?? [];
  if (!sources.includes('synthetic_demo')) return null;
  return (
    <div className="banner" role="note">
      <strong>Demo data.</strong> The model was trained on a <em>synthetic</em> dataset (not measured or DFT values).
      Results illustrate the workflow only and are not scientific findings.
    </div>
  );
}
