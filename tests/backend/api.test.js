import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';
import { createApp } from '../../backend/server.js';
import { openDb } from '../../backend/database/connection.js';

const calls = { discover: 0 };
const fakeMl = {
  predict: async (formulas) => ({
    predictions: formulas.map((f) => (f === 'Xx9'
      ? { input: f, error: 'unsupported elements' }
      : { input: f, formula: f, property: 'band_gap', unit: 'eV', prediction: 2.5, uncertainty: 0.1, confidence: 'high', model_version: 'v1' })),
  }),
  discover: async ({ spec }) => {
    calls.discover += 1;
    if (spec.band_gap?.max === 99) throw new Error('boom');
    const cand = (formula, origin, rank) => ({
      formula, origin, rank, pareto_rank: 0, score: 0.9, prediction: 2, uncertainty: origin === 'known' ? 0 : 0.2,
      confidence: origin === 'known' ? 'recorded' : 'high',
      validation: { overall: 'pass', layers: [] }, explanation: rank === 1 ? { top_features: [] } : undefined,
    });
    return {
      spec, stats: { kept: 2 }, model_version: 'v1',
      known_matches: [cand('ZnS', 'known', 1)],
      novel_candidates: [cand('ZnSe', 'generated', 1), cand('CdS', 'generated', 2)],
    };
  },
  explain: async (formula) => ({ formula, top_features: [] }),
};

let server; let base; let db;
const json = (path, init) => fetch(base + path, init).then(async (r) => ({ status: r.status, body: await r.json() }));
const post = (path, body) => json(path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
const waitForJob = async (id) => {
  for (let i = 0; i < 50; i += 1) {
    const { body } = await json(`/api/discovery/${id}`);
    if (body.status !== 'running') return body;
    await new Promise((r) => setTimeout(r, 20));
  }
  throw new Error('job did not finish');
};

before(async () => {
  db = openDb(':memory:');
  const ins = db.prepare('INSERT INTO materials (formula, band_gap, source, predicted_band_gap, uncertainty) VALUES (?, ?, ?, ?, ?)');
  [['NaCl', 5.0], ['MgO', 4.5], ['GaAs', 0], ['ZnS', 2.1], ['Mg_x', 1.0]].forEach(([f, g]) => ins.run(f, g, 'test', g, 0.1));
  server = createApp({ db, ml: fakeMl }).listen(0);
  base = `http://127.0.0.1:${server.address().port}`;
});
after(() => { server.close(); db.close(); });

describe('materials', () => {
  it('filters, sorts and paginates', async () => {
    const { body } = await json('/api/materials?min_gap=2&sort=-band_gap&limit=2');
    assert.equal(body.total, 3);
    assert.deepEqual(body.items.map((m) => m.formula), ['NaCl', 'MgO']);
  });
  it('treats LIKE wildcards in search as literals', async () => {
    const { body } = await json('/api/materials?q=_');
    assert.deepEqual(body.items.map((m) => m.formula), ['Mg_x']);
  });
  it('validates query params and ids', async () => {
    assert.equal((await json('/api/materials?min_gap=abc')).status, 400);
    assert.equal((await json('/api/materials/abc')).status, 400);
    assert.equal((await json('/api/materials/9999')).status, 404);
  });
  it('reports stats', async () => {
    const { body } = await json('/api/materials/stats');
    assert.equal(body.count, 5);
    assert.ok(body.histogram.length > 0);
  });
});

describe('predict', () => {
  it('returns predictions, passes per-item errors through, and logs history', async () => {
    const { status, body } = await post('/api/predict', { formulas: ['ZnS', 'Xx9'] });
    assert.equal(status, 200);
    assert.equal(body.predictions[0].known_band_gap, 2.1);
    assert.ok(body.predictions[1].error);
    const hist = await json('/api/predict/history');
    assert.equal(hist.body.length, 1);
  });
  it('rejects malformed input', async () => {
    for (const bad of [{}, { formulas: [] }, { formulas: 'MgO' }, { formulas: ['Mg;DROP'] }, { formulas: [1] }]) {
      assert.equal((await post('/api/predict', bad)).status, 400, JSON.stringify(bad));
    }
  });
});

describe('discovery', () => {
  it('runs a job to completion and stores ranked candidates', async () => {
    const { status, body } = await post('/api/discovery', { spec: { band_gap: { min: 1, max: 3 } } });
    assert.equal(status, 202);
    const job = await waitForJob(body.id);
    assert.equal(job.status, 'completed');
    assert.deepEqual(job.novel_candidates.map((c) => c.formula), ['ZnSe', 'CdS']);
    assert.equal(job.known_matches[0].origin, 'known');
    assert.ok(job.novel_candidates[0].explanation);
  });
  it('records failures', async () => {
    const { body } = await post('/api/discovery', { spec: { band_gap: { max: 99 } } });
    const job = await waitForJob(body.id);
    assert.equal(job.status, 'failed');
    assert.match(job.error, /boom/);
  });
  it('rejects invalid specs before starting a job', async () => {
    const before = calls.discover;
    for (const spec of [{}, { band_gap: { min: 3, max: 1 } }, { band_gap: { min: 'x' } }, { exclude_elements: ['fe'] }]) {
      assert.equal((await post('/api/discovery', { spec })).status, 400, JSON.stringify(spec));
    }
    assert.equal(calls.discover, before);
  });
  it('404s for unknown jobs and compares candidates', async () => {
    assert.equal((await json('/api/discovery/9999')).status, 404);
    const { body: list } = await json('/api/discovery');
    const full = await json(`/api/discovery/${list.find((j) => j.status === 'completed').id}`);
    const ids = [...full.body.known_matches, ...full.body.novel_candidates].slice(0, 2).map((c) => c.id);
    const cmp = await json(`/api/candidates/compare?ids=${ids.join(',')}`);
    assert.equal(cmp.body.length, 2);
    assert.equal((await json('/api/candidates/compare?ids=1')).status, 400);
  });
});

describe('misc', () => {
  it('serves models/experiments lists and a JSON 404', async () => {
    assert.deepEqual((await json('/api/models')).body, []);
    assert.deepEqual((await json('/api/experiments')).body, []);
    assert.equal((await json('/api/nope')).status, 404);
  });
  it('returns 400 for invalid JSON bodies', async () => {
    const r = await fetch(`${base}/api/predict`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: '{bad' });
    assert.equal(r.status, 400);
  });
});
