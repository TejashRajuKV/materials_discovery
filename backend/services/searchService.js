import { HttpError, parseJson } from '../utils/helpers.js';
import { specError } from '../middleware/validation.js';

const view = (row) => row && { ...row, spec: parseJson(row.spec) };

export function listSearches(db) {
  return db.prepare('SELECT * FROM saved_searches ORDER BY id DESC').all().map(view);
}

export function saveSearch(db, name, spec) {
  const problem = specError(spec);
  if (problem) throw new HttpError(400, problem);
  const { lastInsertRowid: id } = db.prepare('INSERT INTO saved_searches (name, spec) VALUES (?, ?)')
    .run(name, JSON.stringify(spec));
  return view(db.prepare('SELECT * FROM saved_searches WHERE id = ?').get(id));
}

export function getSearch(db, id) {
  const row = db.prepare('SELECT * FROM saved_searches WHERE id = ?').get(id);
  if (!row) throw new HttpError(404, `saved search ${id} not found`);
  return view(row);
}

export function deleteSearch(db, id) {
  if (!db.prepare('DELETE FROM saved_searches WHERE id = ?').run(id).changes) {
    throw new HttpError(404, `saved search ${id} not found`);
  }
}
