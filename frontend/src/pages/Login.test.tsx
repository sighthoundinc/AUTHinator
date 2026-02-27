import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from './Login';

// Mock the API client
vi.mock('../api/client', () => ({
  authApi: {
    login: vi.fn(),
  },
  mfaApi: {
    totpVerify: vi.fn(),
    webauthnBegin: vi.fn(),
    webauthnComplete: vi.fn(),
  },
}));

// Mock @simplewebauthn/browser
vi.mock('@simplewebauthn/browser', () => ({
  startAuthentication: vi.fn(),
}));

// Mock fetch for SSO providers
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderLogin = (url = '/login') => {
  window.history.pushState({}, '', url);
  return render(
    <BrowserRouter>
      <Login />
    </BrowserRouter>
  );
};

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockFetch.mockResolvedValue({
      json: () => Promise.resolve({ providers: [] }),
    });
  });

  it('should render the login form', () => {
    renderLogin();
    expect(screen.getByText('🔐 AUTHinator')).toBeInTheDocument();
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
  });

  it('should update input values on change', () => {
    renderLogin();
    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'testpass' } });

    expect(usernameInput).toHaveValue('testuser');
    expect(passwordInput).toHaveValue('testpass');
  });

  it('should call authApi.login on form submit and store tokens', async () => {
    const { authApi } = await import('../api/client');
    (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
      access: 'access-token',
      refresh: 'refresh-token',
    });

    renderLogin();

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith('user', 'pass');
    });

    expect(localStorage.getItem('auth_token')).toBe('access-token');
    expect(localStorage.getItem('refresh_token')).toBe('refresh-token');
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('should redirect to redirect URL after login when specified', async () => {
    const { authApi } = await import('../api/client');
    (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
      access: 'access-token',
      refresh: 'refresh-token',
    });

    // Mock window.location.href setter
    const hrefSetter = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { ...window.location, href: '', search: '?redirect=http://example.com' },
      writable: true,
    });
    Object.defineProperty(window.location, 'href', {
      set: hrefSetter,
      get: () => '',
    });

    renderLogin('/login?redirect=http://example.com');

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalled();
    });
  });

  it('should display error message on login failure', async () => {
    const { authApi } = await import('../api/client');
    (authApi.login as ReturnType<typeof vi.fn>).mockRejectedValue({
      response: { data: { detail: 'Invalid credentials' } },
    });

    renderLogin();
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });
  });

  it('should show loading state during submission', async () => {
    const { authApi } = await import('../api/client');
    let resolveLogin: (value: unknown) => void;
    (authApi.login as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => { resolveLogin = resolve; })
    );

    renderLogin();
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(screen.getByText('Signing in...')).toBeInTheDocument();
    });

    resolveLogin!({ access: 'a', refresh: 'r' });
  });

  it('should render SSO providers when available', async () => {
    mockFetch.mockResolvedValue({
      json: () => Promise.resolve({
        providers: [
          { id: 'google', name: 'Google', login_url: '/api/auth/google/login/' },
        ],
      }),
    });

    renderLogin();

    await waitFor(() => {
      expect(screen.getByText('Continue with Google')).toBeInTheDocument();
    });
  });

  it('should render Microsoft SSO provider', async () => {
    mockFetch.mockResolvedValue({
      json: () => Promise.resolve({
        providers: [
          { id: 'microsoft', name: 'Microsoft', login_url: '/api/auth/microsoft/login/' },
        ],
      }),
    });

    renderLogin();

    await waitFor(() => {
      expect(screen.getByText('Continue with Microsoft')).toBeInTheDocument();
    });
  });

  it('should render generic SSO provider', async () => {
    mockFetch.mockResolvedValue({
      json: () => Promise.resolve({
        providers: [
          { id: 'okta', name: 'Okta', login_url: '/api/auth/okta/login/' },
        ],
      }),
    });

    renderLogin();

    await waitFor(() => {
      expect(screen.getByText('Continue with Okta')).toBeInTheDocument();
    });
  });

  it('should handle SSO provider fetch failure gracefully', () => {
    mockFetch.mockRejectedValue(new Error('network'));
    renderLogin();
    // Should render without crashing
    expect(screen.getByText('🔐 AUTHinator')).toBeInTheDocument();
  });

  it('should display the sign-in subtitle', () => {
    renderLogin();
    expect(screen.getByText('Sign in to access your services')).toBeInTheDocument();
  });

  it('should display the footer text', () => {
    renderLogin();
    expect(screen.getByText('Centralized authentication for all your services')).toBeInTheDocument();
  });

  describe('MFA flow', () => {
    it('should show MFA step when login returns mfa_required', async () => {
      const { authApi } = await import('../api/client');
      (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        mfa_required: true,
        mfa_token: 'mfa-tok-123',
        mfa_methods: ['totp'],
      });

      renderLogin();
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
      fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByText('Two-factor authentication required')).toBeInTheDocument();
      });
      expect(screen.getByLabelText('Authenticator Code')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Verify Code' })).toBeInTheDocument();
    });

    it('should show both TOTP and WebAuthn options when both methods available', async () => {
      const { authApi } = await import('../api/client');
      (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        mfa_required: true,
        mfa_token: 'mfa-tok-123',
        mfa_methods: ['totp', 'webauthn'],
      });

      renderLogin();
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
      fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByLabelText('Authenticator Code')).toBeInTheDocument();
      });
      expect(screen.getByText(/Use Security Key/)).toBeInTheDocument();
      expect(screen.getByText('or')).toBeInTheDocument();
    });

    it('should show only WebAuthn when that is the only method', async () => {
      const { authApi } = await import('../api/client');
      (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        mfa_required: true,
        mfa_token: 'mfa-tok-123',
        mfa_methods: ['webauthn'],
      });

      renderLogin();
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
      fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByText(/Use Security Key/)).toBeInTheDocument();
      });
      expect(screen.queryByLabelText('Authenticator Code')).not.toBeInTheDocument();
    });

    it('should complete login after successful TOTP verification', async () => {
      const { authApi, mfaApi } = await import('../api/client');
      (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        mfa_required: true,
        mfa_token: 'mfa-tok-123',
        mfa_methods: ['totp'],
      });
      (mfaApi.totpVerify as ReturnType<typeof vi.fn>).mockResolvedValue({
        access: 'jwt-access',
        refresh: 'jwt-refresh',
      });

      renderLogin();
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
      fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByLabelText('Authenticator Code')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Authenticator Code'), { target: { value: '123456' } });
      fireEvent.click(screen.getByRole('button', { name: 'Verify Code' }));

      await waitFor(() => {
        expect(mfaApi.totpVerify).toHaveBeenCalledWith('mfa-tok-123', '123456');
        expect(localStorage.getItem('auth_token')).toBe('jwt-access');
        expect(localStorage.getItem('refresh_token')).toBe('jwt-refresh');
      });
    });

    it('should show error on TOTP verification failure', async () => {
      const { authApi, mfaApi } = await import('../api/client');
      (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        mfa_required: true,
        mfa_token: 'mfa-tok-123',
        mfa_methods: ['totp'],
      });
      (mfaApi.totpVerify as ReturnType<typeof vi.fn>).mockRejectedValue({
        response: { data: { error: 'Invalid verification code' } },
      });

      renderLogin();
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
      fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByLabelText('Authenticator Code')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Authenticator Code'), { target: { value: '000000' } });
      fireEvent.click(screen.getByRole('button', { name: 'Verify Code' }));

      await waitFor(() => {
        expect(screen.getByText('Invalid verification code')).toBeInTheDocument();
      });
    });

    it('should show validation error when TOTP code is empty', async () => {
      const { authApi } = await import('../api/client');
      (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        mfa_required: true,
        mfa_token: 'mfa-tok-123',
        mfa_methods: ['totp'],
      });

      renderLogin();
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
      fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByLabelText('Authenticator Code')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: 'Verify Code' }));

      await waitFor(() => {
        expect(screen.getByText('Please enter the 6-digit code from your authenticator app')).toBeInTheDocument();
      });
    });

    it('should complete login after successful WebAuthn verification', async () => {
      const { authApi, mfaApi } = await import('../api/client');
      const { startAuthentication } = await import('@simplewebauthn/browser');

      (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        mfa_required: true,
        mfa_token: 'mfa-tok-123',
        mfa_methods: ['webauthn'],
      });
      (mfaApi.webauthnBegin as ReturnType<typeof vi.fn>).mockResolvedValue({
        options: { challenge: 'test-challenge' },
      });
      (startAuthentication as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 'cred-id',
        rawId: 'cred-id',
        type: 'public-key',
      });
      (mfaApi.webauthnComplete as ReturnType<typeof vi.fn>).mockResolvedValue({
        access: 'jwt-access',
        refresh: 'jwt-refresh',
      });

      renderLogin();
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
      fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByText(/Use Security Key/)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Use Security Key/));

      await waitFor(() => {
        expect(mfaApi.webauthnBegin).toHaveBeenCalledWith('mfa-tok-123');
        expect(localStorage.getItem('auth_token')).toBe('jwt-access');
      });
    });

    it('should show error on WebAuthn failure', async () => {
      const { authApi, mfaApi } = await import('../api/client');

      (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        mfa_required: true,
        mfa_token: 'mfa-tok-123',
        mfa_methods: ['webauthn'],
      });
      (mfaApi.webauthnBegin as ReturnType<typeof vi.fn>).mockRejectedValue({
        response: { data: { error: 'Security key verification failed' } },
      });

      renderLogin();
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
      fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByText(/Use Security Key/)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Use Security Key/));

      await waitFor(() => {
        expect(screen.getByText('Security key verification failed')).toBeInTheDocument();
      });
    });

    it('should go back to login form when clicking back', async () => {
      const { authApi } = await import('../api/client');
      (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        mfa_required: true,
        mfa_token: 'mfa-tok-123',
        mfa_methods: ['totp'],
      });

      renderLogin();
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
      fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByText('Two-factor authentication required')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Back to login/));

      await waitFor(() => {
        expect(screen.getByText('Sign in to access your services')).toBeInTheDocument();
      });
      expect(screen.getByLabelText('Username')).toBeInTheDocument();
    });
  });
});
