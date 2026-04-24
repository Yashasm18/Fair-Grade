import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DarkModeToggle from '../../components/DarkModeToggle';

describe('DarkModeToggle', () => {
  it('renders with light mode label when isDark is false', () => {
    render(<DarkModeToggle isDark={false} onToggle={() => {}} />);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Switch to dark mode');
  });

  it('renders with dark mode label when isDark is true', () => {
    render(<DarkModeToggle isDark={true} onToggle={() => {}} />);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Switch to light mode');
  });

  it('calls onToggle when clicked', () => {
    let toggled = false;
    render(<DarkModeToggle isDark={false} onToggle={() => { toggled = true; }} />);
    fireEvent.click(screen.getByRole('button'));
    expect(toggled).toBe(true);
  });

  it('has correct title for light mode', () => {
    render(<DarkModeToggle isDark={false} onToggle={() => {}} />);
    expect(screen.getByRole('button')).toHaveAttribute('title', 'Dark mode');
  });

  it('has correct title for dark mode', () => {
    render(<DarkModeToggle isDark={true} onToggle={() => {}} />);
    expect(screen.getByRole('button')).toHaveAttribute('title', 'Light mode');
  });

  it('adds dark class to track when isDark is true', () => {
    const { container } = render(<DarkModeToggle isDark={true} onToggle={() => {}} />);
    const track = container.querySelector('.toggle-track');
    expect(track?.classList.contains('dark')).toBe(true);
  });

  it('does not add dark class to track when isDark is false', () => {
    const { container } = render(<DarkModeToggle isDark={false} onToggle={() => {}} />);
    const track = container.querySelector('.toggle-track');
    expect(track?.classList.contains('dark')).toBe(false);
  });
});
