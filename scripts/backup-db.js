// Write a consistent snapshot of the SQLite database to database/backups/ and keep the newest N.
//   node scripts/backup-db.js            # keeps the 14 most recent backups
//   node scripts/backup-db.js --keep 30
// Uses VACUUM INTO, which copies a consistent snapshot even while the server is writing.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from '../backend/config/config.js';
import { openDb } from '../backend/database/connection.js';

const keepIndex = process.argv.indexOf('--keep');
const keep = keepIndex >= 0 ? Number(process.argv[keepIndex + 1]) : 14;
if (!Number.isInteger(keep) || keep < 1) {
  console.error('--keep must be a positive integer');
  process.exit(1);
}

const backupDir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'database', 'backups');
fs.mkdirSync(backupDir, { recursive: true });

const stamp = new Date().toISOString().replace(/[:.]/g, '-');
const target = path.join(backupDir, `materials-${stamp}.db`);
const db = openDb(config.dbPath);
db.exec(`VACUUM INTO '${target.replace(/'/g, "''")}'`);
db.close();

const old = fs.readdirSync(backupDir)
  .filter((f) => /^materials-.*\.db$/.test(f))
  .sort()
  .reverse()
  .slice(keep);
for (const file of old) fs.rmSync(path.join(backupDir, file));

console.log(`backup written: ${path.relative(process.cwd(), target)} (${(fs.statSync(target).size / 1e6).toFixed(1)} MB)`);
if (old.length) console.log(`removed ${old.length} old backup(s)`);
