// Run Python with the project's interpreter, forwarding arguments and the exit code.
//   node scripts/run-python.js ml/main.py bootstrap
//   node scripts/run-python.js -m pytest tests/ml -q
import { spawnSync } from 'node:child_process';
import { resolvePython } from './python-bin.js';

const result = spawnSync(resolvePython(), process.argv.slice(2), { stdio: 'inherit' });
if (result.error) {
  console.error(`cannot start Python (${result.error.message}). Set PYTHON_BIN to your interpreter.`);
  process.exit(1);
}
process.exit(result.status ?? 1);
