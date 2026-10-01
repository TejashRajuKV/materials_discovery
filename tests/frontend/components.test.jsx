import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import CandidateTable from '../../frontend/src/components/candidates/CandidateTable.jsx';
import RequirementsForm from '../../frontend/src/components/discovery/RequirementsForm.jsx';
import Histogram from '../../frontend/src/components/charts/Histogram.jsx';
import { fmt, parseElements, prettyFormula } from '../../frontend/src/utils/format.js';

describe('format utils', () => {
  it('formats numbers, formulas and element lists', () => {
    expect(fmt(1.234)).toBe('1.23');
    expect(fmt(null)).toBe('—');
    expect(prettyFormula('Fe2O3')).toBe('Fe₂O₃');
    expect(parseElements('Pb, Cd  Hg')).toEqual(['Pb', 'Cd', 'Hg']);
  });
});

describe('RequirementsForm', () => {
  it('submits the entered requirements', () => {
    const onSubmit = vi.fn();
    render(<RequirementsForm onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText('Exclude elements'), { target: { value: 'Pb, Cd' } });
    fireEvent.change(screen.getByLabelText('Minimum'), { target: { value: '1.5' } });
    fireEvent.click(screen.getByRole('button', { name: /start discovery/i }));
    const spec = onSubmit.mock.calls[0][0];
    expect(spec.band_gap.min).toBe('1.5');
    expect(spec.exclude_elements).toEqual(['Pb', 'Cd']);
  });
});

describe('CandidateTable', () => {
  const candidates = [
    { id: 1, rank: 1, formula: 'ZnS', prediction: 2.1, uncertainty: 0.1, confidence: 'high', pareto_rank: 0, validation: { overall: 'pass' } },
    { id: 2, rank: 2, formula: 'CdS', prediction: 2.4, uncertainty: 0.3, confidence: 'medium', pareto_rank: 1, validation: { overall: 'warn' } },
  ];
  it('lists candidates, toggles comparison and opens details', () => {
    const onToggle = vi.fn();
    const onOpen = vi.fn();
    render(<CandidateTable candidates={candidates} selected={[]} onToggle={onToggle} onOpen={onOpen} />);
    expect(screen.getByText('front')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Compare CdS'));
    expect(onToggle).toHaveBeenCalledWith(2);
    fireEvent.click(screen.getByText('ZnS'));
    expect(onOpen).toHaveBeenCalledWith(candidates[0]);
  });
  it('shows an empty state', () => {
    render(<CandidateTable candidates={[]} selected={[]} />);
    expect(screen.getByText(/no candidates satisfied/i)).toBeInTheDocument();
  });
});

describe('Histogram', () => {
  it('renders one bar per bin', () => {
    const { container } = render(<MemoryRouter><Histogram bins={[{ bin_start: 0, count: 5 }, { bin_start: 0.5, count: 2 }]} /></MemoryRouter>);
    expect(container.querySelectorAll('rect')).toHaveLength(2);
  });
});
