import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock page components to avoid their side effects
vi.mock('./pages/Login', () => ({
  default: () => <div data-testid="login-page">Login Page</div>,
}));
vi.mock('./pages/ServiceDirectory', () => ({
  default: () => <div data-testid="service-directory">Service Directory</div>,
}));

describe('App', () => {
  it('should render the login page at /login', () => {
    window.history.pushState({}, '', '/login');
    render(<App />);
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });

  it('should render the service directory at /', () => {
    window.history.pushState({}, '', '/');
    render(<App />);
    expect(screen.getByTestId('service-directory')).toBeInTheDocument();
  });
});
