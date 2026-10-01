import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from '../config/config.js';
import { openDb } from './connection.js';

/**
 * Consistent online backup (SQLite backup API — safe while the server is writing),
 * keeping only the newest `keep` backups. Returns the new backup's path.
 */
export async function backupDb(db, dir = config.backupsDir, keep = config.backupsToKeep) {
  fs.mkdirSync(dir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const dest = path.join(dir, `materials-${stamp}.db`);
  await db.backup(dest);
  const old = fs.readdirSync(dir).filter((f) => /^materials-.*\.db$/.test(f)).sort().reverse().slice(keep);
  old.forEach((f) => fs.rmSync(path.join(dir, f)));
  return dest;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const db = openDb(config.dbPath);
  backupDb(db).then((dest) => { console.log('backup written to', dest); db.close(); });
}
