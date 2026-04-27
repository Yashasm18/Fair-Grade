import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import AgentPipeline from '../../components/AgentPipeline';

describe('AgentPipeline', () => {
  it('renders the processing title with the file name', () => {
    render(<AgentPipeline currentStep={0} fileName="test_file.jpg" />);
    expect(screen.getByText(/Processing — test_file\.jpg/)).toBeInTheDocument();
  });

  it('renders all 5 agent steps', () => {
    render(<AgentPipeline currentStep={-1} fileName="test.png" />);
    expect(screen.getByText('OCR Agent')).toBeInTheDocument();
    expect(screen.getByText('Privacy Agent')).toBeInTheDocument();
    expect(screen.getByText('Evaluation Agent')).toBeInTheDocument();
    expect(screen.getByText('Bias Agent')).toBeInTheDocument();
    expect(screen.getByText('Reporting Agent')).toBeInTheDocument();
  });

  it('shows server wakeup message at step 0', () => {
    render(<AgentPipeline currentStep={0} fileName="test.png" />);
    expect(screen.getByText(/Waking up secure server/)).toBeInTheDocument();
  });

  it('does not show server wakeup message at step > 0', () => {
    render(<AgentPipeline currentStep={2} fileName="test.png" />);
    expect(screen.queryByText(/Waking up server/)).not.toBeInTheDocument();
  });

  it('marks completed steps correctly', () => {
    const { container } = render(<AgentPipeline currentStep={3} fileName="test.png" />);
    const steps = container.querySelectorAll('.agent-step');
    // Steps 0, 1, 2 should have 'completed' class
    expect(steps[0]?.classList.contains('completed')).toBe(true);
    expect(steps[1]?.classList.contains('completed')).toBe(true);
    expect(steps[2]?.classList.contains('completed')).toBe(true);
    // Step 3 should be 'active'
    expect(steps[3]?.classList.contains('active')).toBe(true);
    // Step 4 should not be completed or active
    expect(steps[4]?.classList.contains('completed')).toBe(false);
    expect(steps[4]?.classList.contains('active')).toBe(false);
  });

  it('sets correct aria-labels for step states', () => {
    render(<AgentPipeline currentStep={2} fileName="test.png" />);
    expect(screen.getByLabelText('OCR Agent: completed')).toBeInTheDocument();
    expect(screen.getByLabelText('Privacy Agent: completed')).toBeInTheDocument();
    expect(screen.getByLabelText('Evaluation Agent: in progress')).toBeInTheDocument();
    expect(screen.getByLabelText('Bias Agent: pending')).toBeInTheDocument();
  });
});
