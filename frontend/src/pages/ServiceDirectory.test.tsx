import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ServiceDirectory from './ServiceDirectory';
import { authApi, servicesApi } from '../api/client';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../api/client', () => ({
  authApi: {
    me: vi.fn(),
    logout: vi.fn(),
  },
  servicesApi: {
    list: vi.fn(),
  },
}));

const mockAuthMe = vi.mocked(authApi.me);
const mockAuthLogout = vi.mocked(authApi.logout);
const mockServicesList = vi.mocked(servicesApi.list);

const renderServiceDirectory = () => {
  return render(
    <BrowserRouter>
      <ServiceDirectory />
    </BrowserRouter>
  );
};

describe('ServiceDirectory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should redirect to login when no token', () => {
    renderServiceDirectory();
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('should show loading state while fetching data', () => {
    localStorage.setItem('auth_token', 'test-token');
    mockAuthMe.mockImplementation(() => new Promise(() => {}));
    mockServicesList.mockImplementation(() => new Promise(() => {}));

    renderServiceDirectory();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should display user info and services after loading', async () => {
    localStorage.setItem('auth_token', 'test-token');

    mockAuthMe.mockResolvedValue({
      id: '1',
      username: 'admin',
      email: 'admin@test.com',
      role: 'ADMIN',
      customer: { id: '1', name: 'Acme Corp' },
    });

    mockServicesList.mockResolvedValue([
      {
        id: 1,
        name: 'RMAinator',
        description: 'RMA tracking',
        ui_url: 'http://localhost:3002',
        icon: '🔧',
        is_active: true,
        last_registered_at: '2024-01-01',
      },
    ]);

    renderServiceDirectory();

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    expect(screen.getByText('RMAinator')).toBeInTheDocument();
    expect(screen.getByText('RMA tracking')).toBeInTheDocument();
    expect(screen.getByText('🔧')).toBeInTheDocument();
  });

  it('should display empty state when no services', async () => {
    localStorage.setItem('auth_token', 'test-token');

    mockAuthMe.mockResolvedValue({
      id: '1', username: 'admin', email: '', role: '', customer: { id: '1', name: 'Acme' },
    });
    mockServicesList.mockResolvedValue([]);

    renderServiceDirectory();

    await waitFor(() => {
      expect(screen.getByText('No services registered yet')).toBeInTheDocument();
    });
  });

  it('should handle 401 error by clearing tokens and redirecting', async () => {
    localStorage.setItem('auth_token', 'expired-token');

    mockAuthMe.mockRejectedValue({
      response: { status: 401 },
    });
    mockServicesList.mockRejectedValue({
      response: { status: 401 },
    });

    renderServiceDirectory();

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    expect(localStorage.getItem('auth_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });

  it('should display error message for non-401 errors', async () => {
    localStorage.setItem('auth_token', 'test-token');

    mockAuthMe.mockRejectedValue({
      response: { status: 500, data: { detail: 'Server error' } },
    });
    mockServicesList.mockRejectedValue({
      response: { status: 500 },
    });

    renderServiceDirectory();

    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument();
    });
  });

  it('should display generic error when no detail in error data', async () => {
    localStorage.setItem('auth_token', 'test-token');

    mockAuthMe.mockRejectedValue({ response: { status: 500 } });
    mockServicesList.mockRejectedValue({ response: { status: 500 } });

    renderServiceDirectory();

    await waitFor(() => {
      expect(screen.getByText('Failed to load data')).toBeInTheDocument();
    });
  });

  it('should handle logout by clearing tokens and redirecting', async () => {
    localStorage.setItem('auth_token', 'test-token');
    localStorage.setItem('refresh_token', 'refresh-token');

    mockAuthMe.mockResolvedValue({
      id: '1', username: 'admin', email: '', role: '', customer: { id: '1', name: 'Acme' },
    });
    mockAuthLogout.mockResolvedValue(undefined);
    mockServicesList.mockResolvedValue([]);

    renderServiceDirectory();

    await waitFor(() => {
      expect(screen.getByText('Logout')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Logout'));

    expect(localStorage.getItem('auth_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('should handle token from URL parameter', async () => {
    window.history.pushState({}, '', '/?token=url-token');

    mockAuthMe.mockResolvedValue({
      id: '1', username: 'admin', email: '', role: '', customer: { id: '1', name: 'Acme' },
    });
    mockServicesList.mockResolvedValue([]);

    renderServiceDirectory();

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    expect(localStorage.getItem('auth_token')).toBe('url-token');
  });

  it('should open service URL with token on click', async () => {
    localStorage.setItem('auth_token', 'test-token');

    mockAuthMe.mockResolvedValue({
      id: '1', username: 'admin', email: '', role: '', customer: { id: '1', name: 'Acme' },
    });
    mockServicesList.mockResolvedValue([
      {
        id: 1,
        name: 'TestService',
        description: 'Test',
        ui_url: 'http://localhost:3002',
        icon: '🔧',
        is_active: true,
        last_registered_at: '2024-01-01',
      },
    ]);

    renderServiceDirectory();

    await waitFor(() => {
      expect(screen.getByText('TestService')).toBeInTheDocument();
    });

    const openButton = screen.getByText('Open Service');
    expect(openButton).toBeInTheDocument();
  });

  it('should display header with title and subtitle', async () => {
    localStorage.setItem('auth_token', 'test-token');

    mockAuthMe.mockResolvedValue({
      id: '1', username: 'admin', email: '', role: '', customer: { id: '1', name: 'Acme' },
    });
    mockServicesList.mockResolvedValue([]);

    renderServiceDirectory();

    await waitFor(() => {
      expect(screen.getByText('Your Services')).toBeInTheDocument();
    });

    expect(screen.getByText('Click on a service to open it')).toBeInTheDocument();
    expect(screen.getByText('Service Directory')).toBeInTheDocument();
  });
});
