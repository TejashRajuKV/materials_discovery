import { useEffect, useState } from 'react';
import { getJob } from '../services/discoveryService.js';

/** Poll a discovery job until it leaves the `running` state. */
export function useJob(id, intervalMs = 1500) {
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    let timer;
    setJob(null);
    setError(null);
    const tick = async () => {
      try {
        const data = await getJob(id);
        if (cancelled) return;
        setJob(data);
        if (data.status === 'running') timer = setTimeout(tick, intervalMs);
      } catch (e) {
        if (!cancelled) setError(e);
      }
    };
    tick();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [id, intervalMs]);

  return { job, error };
}
