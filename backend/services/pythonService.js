import { spawn } from 'node:child_process';
import { config } from '../config/config.js';
import { HttpError } from '../utils/helpers.js';

/**
 * The ML engine can be reached two ways, with the same results and errors:
 *   - spawn: `python ml/main.py <cmd>` per call (default; loads the models on every call)
 *   - service: the resident server `python ml/service.py`, when ML_SERVICE_URL is set (loads them once)
 */

/** Turn an ML result document into the value, or throw the matching HTTP error. */
function unwrap(doc) {
  if (doc.error) {
    const status = doc.error === 'ModelNotTrainedError' ? 503
      : ['InvalidSpecError', 'InvalidMaterialError'].includes(doc.error) ? 400 : 500;
    throw new HttpError(status, doc.message || doc.error);
  }
  return doc;
}

/**
 * Run one ML-engine command (`python ml/main.py <args>`), optionally feeding JSON on stdin.
 * Resolves to the parsed JSON document the CLI prints on stdout.
 */
export function runMl(args, input) {
  return new Promise((resolve, reject) => {
    const child = spawn(config.pythonBin, [config.mlEntry, ...args], { cwd: config.root });
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => {
      child.kill('SIGKILL');
      reject(new HttpError(504, `ML engine timed out after ${config.mlTimeoutMs} ms`));
    }, config.mlTimeoutMs);

    child.stdout.on('data', (d) => { stdout += d; });
    child.stderr.on('data', (d) => { stderr += d; });
    child.on('error', (err) => {
      clearTimeout(timer);
      reject(new HttpError(503, `cannot start ML engine (${config.pythonBin}): ${err.message}`));
    });
    child.on('close', () => {
      clearTimeout(timer);
      let doc;
      try {
        doc = JSON.parse(stdout.trim().split('\n').pop());
      } catch {
        return reject(new HttpError(502, 'ML engine returned invalid output', stderr.slice(-500)));
      }
      try {
        resolve(unwrap(doc));
      } catch (err) {
        reject(err);
      }
    });
    if (input !== undefined) child.stdin.write(JSON.stringify(input));
    child.stdin.end();
  });
}

/** POST to the resident ML service and return its result document. */
async function callService(endpoint, body) {
  let res;
  try {
    res = await fetch(`${config.mlServiceUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body ?? {}),
      signal: AbortSignal.timeout(config.mlTimeoutMs),
    });
  } catch (err) {
    if (err.name === 'TimeoutError') throw new HttpError(504, `ML service timed out after ${config.mlTimeoutMs} ms`);
    throw new HttpError(503, `ML service unreachable at ${config.mlServiceUrl}: ${err.message}`);
  }
  try {
    return unwrap(await res.json());
  } catch (err) {
    if (err instanceof HttpError) throw err;
    throw new HttpError(502, 'ML service returned invalid output');
  }
}

export const defaultMl = {
  predict: (formulas, property = 'band_gap') => (config.mlServiceUrl
    ? callService('/predict', { formulas, property })
    : runMl(['predict', '--stdin'], { formulas, property })),
  discover: (payload) => (config.mlServiceUrl
    ? callService('/discover', payload)
    : runMl(['discover', '--stdin'], payload)),
  explain: (formula) => (config.mlServiceUrl
    ? callService('/explain', { formula })
    : runMl(['explain', '--formula', formula])),
};
