import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Footer from '../../components/Footer';

describe('Footer', () => {
  it('renders the FairGrade AI brand', () => {
    render(<Footer />);
    expect(screen.getByText('FairGrade AI')).toBeInTheDocument();
  });

  it('renders the SDG 4 badge', () => {
    render(<Footer />);
    expect(screen.getByText('Quality Education')).toBeInTheDocument();
    expect(screen.getByText('SDG 4')).toBeInTheDocument();
  });

  it('renders the Gemini badge', () => {
    render(<Footer />);
    expect(screen.getByText('Built with Gemini')).toBeInTheDocument();
  });

  it('renders the Google Solution Challenge year', () => {
    render(<Footer />);
    expect(screen.getByText('Google Solution Challenge 2026')).toBeInTheDocument();
  });

  it('renders the team name', () => {
    render(<Footer />);
    expect(screen.getByText(/Team VEKTOR/)).toBeInTheDocument();
  });
});
