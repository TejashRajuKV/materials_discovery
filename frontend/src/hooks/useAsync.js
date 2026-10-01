import { useCallback, useEffect, useState } from 'react';

/** Run an async loader on mount / when deps change. Ignores results from stale runs. */
export function useAsync(loader, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    loader(controller.signal)
      .then((data) => !controller.signal.aborted && setState({ data, error: null, loading: false }))
      .catch((error) => !controller.signal.aborted && setState({ data: null, error, loading: false }));
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { ...state, reload };
}
