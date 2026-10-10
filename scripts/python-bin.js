import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

/**
 * Pick the Python interpreter for the ML engine, in order:
 *   1. PYTHON_BIN, if set
 *   2. the project's virtualenv (.venv), on Windows or POSIX
 *   3. `python` on Windows, `python3` elsewhere
 * The Windows `python3` name is often a Microsoft Store alias that prints an error, so it is avoided.
 */
export function resolvePython(env = process.env) {
  if (env.PYTHON_BIN) return env.PYTHON_BIN;
  const candidates = [
    path.join(root, '.venv', 'Scripts', 'python.exe'),
    path.join(root, '.venv', 'bin', 'python'),
  ];
  const venv = candidates.find((p) => fs.existsSync(p));
  if (venv) return venv;
  return process.platform === 'win32' ? 'python' : 'python3';
}
