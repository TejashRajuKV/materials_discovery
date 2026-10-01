import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { describe, it } from 'node:test';
import { backupDb } from '../../backend/database/backup.js';
import { openDb } from '../../backend/database/connection.js';
import { rateLimit } from '../../backend/middleware/security.js';
import { createApp } from '../../backend/server.js';
import { failInterruptedJobs, startJob } from '../../backend/services/discoveryService.js';

const never = () => new Promise(() => {}); // an ML call that never finishes

describe('rate limiting', () => {
  it('blocks after max requests and recovers in the next window', () => {
    let t = 0;
    const limiter = rateLimit({ windowMs: 1000, max: 2, now: () => t });
    const call = () => {
      let err;
      limiter({ ip: '1.2.3.4' }, { set() {} }, (e) => { err = e; });
      return err;
    };
    assert.equal(call(), undefined);
    assert.equal(call(), undefined);
    assert.equal(call().status, 429);
    t = 1001;
    assert.equal(call(), undefined);
  });

  it('applies to POST /api/predict via the app', async () => {
    const db = openDb(':memory:');
    const ml = { predict: async () => ({ predictions: [] }) };
    const server = createApp({ db, ml, limits: { windowMs: 60_000, predictPerWindow: 2, discoveryPerWindow: 5 } }).listen(0);
    const url = `http://127.0.0.1:${server.address().port}/api/predict`;
    const post = () => fetch(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ formulas: ['NaCl'] }) });
    assert.equal((await post()).status, 200);
    assert.equal((await post()).status, 200);
    const blocked = await post();
    assert.equal(blocked.status, 429);
    assert.ok(blocked.headers.get('retry-after'));
    server.close();
  });
});

describe('job safety', () => {
  it('caps concurrent discovery jobs', () => {
    const db = openDb(':memory:');
    const ml = { discover: never };
    startJob(db, ml, { band_gap: { min: 1 } });
    startJob(db, ml, { band_gap: { min: 1 } });
    assert.throws(() => startJob(db, ml, { band_gap: { min: 1 } }), (e) => e.status === 429);
  });

  it('marks jobs left running by a dead process as failed', () => {
    const db = openDb(':memory:');
    startJob(db, { discover: never }, { band_gap: { min: 1 } });
    assert.equal(failInterruptedJobs(db), 1);
    const row = db.prepare('SELECT status, error FROM discovery_jobs').get();
    assert.deepEqual({ ...row }, { status: 'failed', error: 'interrupted by server restart' });
    assert.equal(failInterruptedJobs(db), 0);
  });
});

describe('backup', () => {
  it('writes a restorable copy and prunes old backups', async () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'bk-'));
    const db = openDb(path.join(dir, 'src.db'));
    db.prepare('INSERT INTO materials (formula, band_gap) VALUES (?, ?)').run('NaCl', 5);
    for (let i = 0; i < 3; i += 1) {
      await backupDb(db, path.join(dir, 'backups'), 2);
      await new Promise((r) => setTimeout(r, 5));
    }
    const files = fs.readdirSync(path.join(dir, 'backups'));
    assert.equal(files.length, 2);
    const copy = openDb(path.join(dir, 'backups', files[0]));
    assert.equal(copy.prepare('SELECT formula FROM materials').get().formula, 'NaCl');
    copy.close(); db.close();
    fs.rmSync(dir, { recursive: true });
  });
});
