import { spawn } from 'node:child_process';
import { config } from '../config/config.js';
import { HttpError } from '../utils/helpers.js';

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
      if (doc.error) {
        const status = doc.error === 'ModelNotTrainedError' ? 503
          : ['InvalidSpecError', 'InvalidMaterialError'].includes(doc.error) ? 400 : 500;
        return reject(new HttpError(status, doc.message || doc.error));
      }
      resolve(doc);
    });
    if (input !== undefined) child.stdin.write(JSON.stringify(input));
    child.stdin.end();
  });
}

export const defaultMl = {
  predict: (formulas) => runMl(['predict', '--stdin'], { formulas }),
  discover: (payload) => runMl(['discover', '--stdin'], payload),
  explain: (formula) => runMl(['explain', '--formula', formula]),
};
