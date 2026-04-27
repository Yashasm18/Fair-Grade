import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ResultCard from '../../components/ResultCard';
import type { FileResult } from '../../types';

const mockTruncateName = (name: string, max: number = 28): string => {
  if (name.length <= max) return name;
  const ext = name.substring(name.lastIndexOf('.'));
  return name.substring(0, max - ext.length - 3) + '...' + ext;
};

const mockResult: FileResult = {
  fileName: 'test_answer.jpg',
  data: {
    originalTextLength: 200,
    anonymizedText: 'The answer text goes here after anonymization.',
    evaluation: {
      aiScore: 8,
      teacherScore: 6,
      explanation: 'Good understanding of the topic with minor gaps.',
      confidenceScore: 0.92,
    },
    bias: {
      level: 'Medium',
      status: 'Undergraded',
      gap: 2,
      biasScorePercentage: 25.0,
      formulaUsed: 'Test formula',
    },
    verified: false,
  },
  error: null,
};

const errorResult: FileResult = {
  fileName: 'failed_answer.jpg',
  data: null,
  error: 'Network error: Failed to fetch',
};

describe('ResultCard', () => {
  it('renders student ID and scores', () => {
    render(
      <ResultCard
        result={mockResult}
        studentId="STU-001"
        onRetry={null}
        onVerify={vi.fn()}
        truncateName={mockTruncateName}
      />
    );
    expect(screen.getByText('STU-001')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument(); // AI score
    expect(screen.getByText('6')).toBeInTheDocument(); // Teacher score
  });

  it('renders bias indicator', () => {
    render(
      <ResultCard
        result={mockResult}
        studentId="STU-001"
        onRetry={null}
        onVerify={vi.fn()}
        truncateName={mockTruncateName}
      />
    );
    expect(screen.getByText('Medium Risk')).toBeInTheDocument();
    expect(screen.getByText(/Undergraded/)).toBeInTheDocument();
  });

  it('renders confidence score', () => {
    render(
      <ResultCard
        result={mockResult}
        studentId="STU-001"
        onRetry={null}
        onVerify={vi.fn()}
        truncateName={mockTruncateName}
      />
    );
    expect(screen.getByText('Confidence: 92%')).toBeInTheDocument();
  });

  it('renders error state with retry button', () => {
    const onRetry = vi.fn();
    render(
      <ResultCard
        result={errorResult}
        studentId="STU-002"
        onRetry={onRetry}
        onVerify={vi.fn()}
        truncateName={mockTruncateName}
      />
    );
    expect(screen.getAllByText(/Failed/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Network error: Failed to fetch')).toBeInTheDocument();
    
    const retryBtn = screen.getByText('Retry');
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledWith('failed_answer.jpg');
  });

  it('shows teacher verification controls when not verified', () => {
    render(
      <ResultCard
        result={mockResult}
        studentId="STU-001"
        onRetry={null}
        onVerify={vi.fn()}
        truncateName={mockTruncateName}
      />
    );
    expect(screen.getByText('Accept AI Score')).toBeInTheDocument();
    expect(screen.getByText('Override Score')).toBeInTheDocument();
  });

  it('calls onVerify with accept_ai when Accept AI Score is clicked', () => {
    const onVerify = vi.fn();
    render(
      <ResultCard
        result={mockResult}
        studentId="STU-001"
        onRetry={null}
        onVerify={onVerify}
        truncateName={mockTruncateName}
      />
    );
    
    fireEvent.click(screen.getByText('Accept AI Score'));
    expect(onVerify).toHaveBeenCalledWith('test_answer.jpg', expect.objectContaining({
      action: 'accept_ai',
      finalScore: 8,
    }));
  });

  it('shows override form when Override Score is clicked', () => {
    render(
      <ResultCard
        result={mockResult}
        studentId="STU-001"
        onRetry={null}
        onVerify={vi.fn()}
        truncateName={mockTruncateName}
      />
    );
    
    fireEvent.click(screen.getByText('Override Score'));
    expect(screen.getByPlaceholderText('Final score (0-10)')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Reason for override (optional)')).toBeInTheDocument();
  });

  it('renders anonymized text and AI explanation', () => {
    render(
      <ResultCard
        result={mockResult}
        studentId="STU-001"
        onRetry={null}
        onVerify={vi.fn()}
        truncateName={mockTruncateName}
      />
    );
    expect(screen.getByText('The answer text goes here after anonymization.')).toBeInTheDocument();
    expect(screen.getByText('Good understanding of the topic with minor gaps.')).toBeInTheDocument();
  });

  it('renders weighted bias percentage', () => {
    render(
      <ResultCard
        result={mockResult}
        studentId="STU-001"
        onRetry={null}
        onVerify={vi.fn()}
        truncateName={mockTruncateName}
      />
    );
    expect(screen.getByText('25%')).toBeInTheDocument();
  });
});
