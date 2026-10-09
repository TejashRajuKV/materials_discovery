import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';

const schemaPath = path.join(path.dirname(fileURLToPath(import.meta.url)), 'schema.sql');

/** Add columns that databases created before they existed do not have (CREATE TABLE IF NOT EXISTS skips them). */
function migrate(db) {
  const columns = (table) => db.prepare(`PRAGMA table_info(${table})`).all().map((c) => c.name);
  if (!columns('candidates').includes('properties')) {
    db.exec('ALTER TABLE candidates ADD COLUMN properties TEXT');
  }
}

/**
 * Open (and migrate) a SQLite database. Pass ':memory:' for tests.
 * Uses the built-in node:sqlite module (no native build), and adds the two helpers the
 * rest of the backend relies on: `db.transaction(fn)` and `db.pragma(text)`.
 */
export function openDb(dbPath) {
  if (dbPath !== ':memory:') fs.mkdirSync(path.dirname(dbPath), { recursive: true });
  const db = new DatabaseSync(dbPath);
  db.pragma = (text) => db.exec(`PRAGMA ${text}`);
  db.transaction = (fn) => (...args) => {
    db.exec('BEGIN');
    try {
      const result = fn(...args);
      db.exec('COMMIT');
      return result;
    } catch (err) {
      db.exec('ROLLBACK');
      throw err;
    }
  };
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  db.exec(fs.readFileSync(schemaPath, 'utf8'));
  migrate(db);
  return db;
}
