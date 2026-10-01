import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Candidates from '../../frontend/src/pages/Candidates/index.jsx';
import Prediction from '../../frontend/src/pages/Prediction/index.jsx';

const reply = (data, ok = true, status = 200) => Promise.resolve({ ok, status, json: () => Promise.resolve(data) });
const mockApi = (routes) => vi.stubGlobal('fetch', vi.fn((url, init) => {
  const key = Object.keys(routes).find((k) => String(url).includes(k));
  if (!key) return reply({ error: `unmocked ${url}` }, false, 404);
  const value = routes[key];
  return typeof value === 'function' ? value(url, init) : reply(value);
}));

beforeEach(() => vi.unstubAllGlobals());
afterEach(() => vi.unstubAllGlobals());

describe('Prediction page', () => {
  it('sends the parsed formulas and shows the prediction with its interval', async () => {
    mockApi({
      '/api/predict': (url, init) => {
        expect(JSON.parse(init.body)).toEqual({ formulas: ['MgO', 'ZnS'] });
        return reply({ predictions: [
          { input: 'MgO', formula: 'MgO', prediction: 4.57, uncertainty: 0.34, confidence: 'medium', model: 'rf', interval: [3.96, 5.18], interval_level: 0.9 },
          { input: 'ZnS', error: 'unsupported' },
        ] });
      },
    });
    render(<Prediction />);
    fireEvent.change(screen.getByLabelText('Formulas'), { target: { value: 'MgO, ZnS' } });
    fireEvent.click(screen.getByRole('button', { name: /predict band gap/i }));
    expect(await screen.findByText(/90% interval: 3\.96–5\.18 eV/)).toBeInTheDocument();
    expect(screen.getByText('unsupported')).toBeInTheDocument();
  });

  it('shows API errors', async () => {
    mockApi({ '/api/predict': () => reply({ error: 'ML engine timed out' }, false, 504) });
    render(<Prediction />);
    fireEvent.click(screen.getByRole('button', { name: /predict band gap/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('ML engine timed out');
  });
});

describe('Candidates page', () => {
  const candidate = (id, formula, origin, rank) => ({
    id, formula, origin, rank, pareto_rank: 0, score: 0.9, prediction: 2.0, uncertainty: 0.2, confidence: 'high',
    objectives: { gap_distance: 0.1, uncertainty: 0.2 }, validation: { overall: 'pass', layers: [] }, explanation: null,
  });
  const job = {
    id: 7, status: 'completed', model_version: 'v1', spec: {},
    stats: { known_considered: 10, generated_considered: 5, satisfied_requirements: 3, failed_validation: 0, generated_kept: 2, known_kept: 1 },
    novel_candidates: [candidate(1, 'ZnSe', 'generated', 1), candidate(2, 'CdS', 'generated', 2)],
    known_matches: [candidate(3, 'ZnS', 'known', 1)],
  };
  const renderAt = () => render(
    <MemoryRouter initialEntries={['/discovery/7']}>
      <Routes><Route path="/discovery/:id" element={<Candidates />} /></Routes>
    </MemoryRouter>,
  );

  it('shows novel candidates first and switches to known matches', async () => {
    mockApi({ '/api/discovery/7': job });
    renderAt();
    expect(await screen.findByText('top 2 of 2', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('ZnSe')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: /known matches/i }));
    expect(screen.getByText('ZnS')).toBeInTheDocument();
    expect(screen.queryByText('ZnSe')).not.toBeInTheDocument();
  });

  it('polls a running job until it completes', async () => {
    let calls = 0;
    mockApi({ '/api/discovery/7': () => reply(++calls < 2 ? { ...job, status: 'running', stats: null } : job) });
    renderAt();
    expect(await screen.findByText(/screening and ranking/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('ZnSe')).toBeInTheDocument(), { timeout: 4000 });
    expect(calls).toBeGreaterThanOrEqual(2);
  });

  it('reports a failed job', async () => {
    mockApi({ '/api/discovery/7': { ...job, status: 'failed', error: 'boom' } });
    renderAt();
    expect(await screen.findByRole('alert')).toHaveTextContent('boom');
  });
});
