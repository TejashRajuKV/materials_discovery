import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Database from 'better-sqlite3';

const schemaPath = path.join(path.dirname(fileURLToPath(import.meta.url)), 'schema.sql');

/** Open (and migrate) a SQLite database. Pass ':memory:' for tests. */
export function openDb(dbPath) {
  if (dbPath !== ':memory:') fs.mkdirSync(path.dirname(dbPath), { recursive: true });
  const db = new Database(dbPath);
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  db.exec(fs.readFileSync(schemaPath, 'utf8'));
  return db;
}
