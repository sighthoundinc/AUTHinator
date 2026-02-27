import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Profile from './Profile';

// Mock the API client
vi.mock('../api/client', () => ({
  authApi: {
    me: vi.fn(),
  },
  totpApi: {
    status: vi.fn(),
    setup: vi.fn(),
    confirm: vi.fn(),
    disable: vi.fn(),
  },
  webauthnApi: {
    listCredentials: vi.fn(),
    registerBegin: vi.fn(),
    registerComplete: vi.fn(),
    deleteCredential: vi.fn(),
  },
}));

// Mock @simplewebauthn/browser
vi.mock('@simplewebauthn/browser', () => ({
  startRegistration: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderProfile = () =>
  render(
    <BrowserRouter>
      <Profile />
    </BrowserRouter>
  );

describe('Profile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('auth_token', 'test-token');
  });

  it('should redirect to login if no token', () => {
    localStorage.removeItem('auth_token');
    renderProfile();
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('should show loading spinner initially', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {})
    );
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();
    // Spinner is a div with border-b-2 class — just check main content isn't rendered yet
    expect(screen.queryByText('Account Information')).not.toBeInTheDocument();
  });

  it('should display user profile information', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'testuser',
      email: 'test@example.com',
      role: 'CUSTOMER_USER',
      customer: { id: '1', name: 'Test Corp' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByText('testuser')).toBeInTheDocument();
    });
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('CUSTOMER_USER')).toBeInTheDocument();
    expect(screen.getByText('Test Corp')).toBeInTheDocument();
  });

  it('should show Enable 2FA button when TOTP is not enabled', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Enable 2FA' })).toBeInTheDocument();
    });
  });

  it('should show Enabled badge and Disable button when TOTP is enabled', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: true });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByText('✓ Enabled')).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: 'Disable 2FA' })).toBeInTheDocument();
  });

  it('should show QR code when Enable 2FA is clicked', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (totpApi.setup as ReturnType<typeof vi.fn>).mockResolvedValue({
      qr_code: 'data:image/png;base64,TESTQR',
      secret: 'TESTSECRET',
    });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Enable 2FA' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Enable 2FA' }));

    await waitFor(() => {
      expect(screen.getByText('Scan QR Code')).toBeInTheDocument();
    });
    expect(screen.getByAltText('TOTP QR Code')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Verify & Enable' })).toBeInTheDocument();
  });

  it('should confirm TOTP with valid code', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (totpApi.setup as ReturnType<typeof vi.fn>).mockResolvedValue({
      qr_code: 'data:image/png;base64,QR', secret: 'SECRET',
    });
    (totpApi.confirm as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Enable 2FA' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Enable 2FA' }));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter 6-digit code')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText('Enter 6-digit code'), {
      target: { value: '123456' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Verify & Enable' }));

    await waitFor(() => {
      expect(totpApi.confirm).toHaveBeenCalledWith('123456');
    });
    expect(screen.getByText('Two-factor authentication enabled successfully')).toBeInTheDocument();
  });

  it('should show disable TOTP form and disable successfully', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: true });
    (totpApi.disable as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Disable 2FA' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Disable 2FA' }));

    await waitFor(() => {
      expect(screen.getByText('Disable Two-Factor Authentication')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText('Enter 6-digit code'), {
      target: { value: '654321' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Disable 2FA/i }));

    await waitFor(() => {
      expect(totpApi.disable).toHaveBeenCalledWith('654321');
    });
  });

  it('should display existing WebAuthn credentials', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([
      { id: 1, name: 'YubiKey', created_at: '2025-01-15T00:00:00Z' },
    ]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/YubiKey/)).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: 'Remove' })).toBeInTheDocument();
  });

  it('should show add security key form', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Add Security Key' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Add Security Key' }));

    expect(screen.getByPlaceholderText('e.g., YubiKey, Touch ID')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add Key' })).toBeInTheDocument();
  });

  it('should show error when adding key without name', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Add Security Key' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Add Security Key' }));
    fireEvent.click(screen.getByRole('button', { name: 'Add Key' }));

    expect(screen.getByText('Please enter a name for this security key')).toBeInTheDocument();
  });

  it('should navigate back when clicking Back button', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByText('← Back')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('← Back'));
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('should handle API error on load gracefully', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network error'));
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('should show error when confirming TOTP without entering code', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (totpApi.setup as ReturnType<typeof vi.fn>).mockResolvedValue({
      qr_code: 'data:image/png;base64,QR', secret: 'S',
    });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Enable 2FA' })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enable 2FA' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Verify & Enable' })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Verify & Enable' }));

    expect(screen.getByText('Please enter the 6-digit code from your authenticator app')).toBeInTheDocument();
  });

  it('should show error when disabling TOTP without entering code', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: true });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Disable 2FA' })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Disable 2FA' }));

    await waitFor(() => {
      expect(screen.getByText('Disable Two-Factor Authentication')).toBeInTheDocument();
    });

    // Click the Disable 2FA button inside the form (not the header one)
    const disableButtons = screen.getAllByRole('button', { name: /Disable 2FA/i });
    fireEvent.click(disableButtons[disableButtons.length - 1]);

    expect(screen.getByText('Please enter the 6-digit code from your authenticator app')).toBeInTheDocument();
  });

  it('should cancel TOTP setup', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (totpApi.setup as ReturnType<typeof vi.fn>).mockResolvedValue({
      qr_code: 'data:image/png;base64,QR', secret: 'S',
    });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Enable 2FA' })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enable 2FA' }));

    await waitFor(() => {
      expect(screen.getByText('Scan QR Code')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByText('Scan QR Code')).not.toBeInTheDocument();
  });

  it('should cancel WebAuthn add form', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Add Security Key' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Add Security Key' }));
    expect(screen.getByPlaceholderText('e.g., YubiKey, Touch ID')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByPlaceholderText('e.g., YubiKey, Touch ID')).not.toBeInTheDocument();
  });

  it('should redirect to login on 401 error', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    const err = { response: { status: 401 } };
    (authApi.me as ReturnType<typeof vi.fn>).mockRejectedValue(err);
    (totpApi.status as ReturnType<typeof vi.fn>).mockRejectedValue(err);
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockRejectedValue(err);

    renderProfile();

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('should handle TOTP setup error', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (totpApi.setup as ReturnType<typeof vi.fn>).mockRejectedValue({
      response: { data: { error: 'Setup failed' } },
    });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Enable 2FA' })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enable 2FA' }));

    await waitFor(() => {
      expect(screen.getByText('Setup failed')).toBeInTheDocument();
    });
  });

  it('should handle TOTP confirm error', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (totpApi.setup as ReturnType<typeof vi.fn>).mockResolvedValue({
      qr_code: 'data:image/png;base64,QR', secret: 'S',
    });
    (totpApi.confirm as ReturnType<typeof vi.fn>).mockRejectedValue({
      response: { data: { error: 'Invalid code' } },
    });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Enable 2FA' })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enable 2FA' }));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter 6-digit code')).toBeInTheDocument();
    });
    fireEvent.change(screen.getByPlaceholderText('Enter 6-digit code'), {
      target: { value: '000000' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Verify & Enable' }));

    await waitFor(() => {
      expect(screen.getByText('Invalid code')).toBeInTheDocument();
    });
  });

  it('should handle TOTP disable error', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: true });
    (totpApi.disable as ReturnType<typeof vi.fn>).mockRejectedValue({
      response: { data: { error: 'Bad token' } },
    });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Disable 2FA' })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Disable 2FA' }));

    await waitFor(() => {
      expect(screen.getByText('Disable Two-Factor Authentication')).toBeInTheDocument();
    });
    fireEvent.change(screen.getByPlaceholderText('Enter 6-digit code'), {
      target: { value: '999999' },
    });
    const disableButtons = screen.getAllByRole('button', { name: /Disable 2FA/i });
    fireEvent.click(disableButtons[disableButtons.length - 1]);

    await waitFor(() => {
      expect(screen.getByText('Bad token')).toBeInTheDocument();
    });
  });

  it('should cancel TOTP disable form', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: true });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Disable 2FA' })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Disable 2FA' }));

    await waitFor(() => {
      expect(screen.getByText('Disable Two-Factor Authentication')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByText('Disable Two-Factor Authentication')).not.toBeInTheDocument();
  });

  it('should delete a WebAuthn credential', async () => {
    vi.stubGlobal('confirm', vi.fn(() => true));
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([
      { id: 1, name: 'YubiKey', created_at: '2025-01-15T00:00:00Z' },
    ]);
    (webauthnApi.deleteCredential as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);

    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/YubiKey/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));

    await waitFor(() => {
      expect(webauthnApi.deleteCredential).toHaveBeenCalledWith(1);
    });
    expect(screen.getByText('Security key removed successfully')).toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it('should handle WebAuthn delete error', async () => {
    vi.stubGlobal('confirm', vi.fn(() => true));
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([
      { id: 1, name: 'YubiKey', created_at: '2025-01-15T00:00:00Z' },
    ]);
    (webauthnApi.deleteCredential as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('fail'));

    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/YubiKey/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));

    await waitFor(() => {
      expect(screen.getByText('Failed to remove security key')).toBeInTheDocument();
    });
    vi.unstubAllGlobals();
  });

  it('should handle WebAuthn add error', async () => {
    const { authApi, totpApi, webauthnApi } = await import('../api/client');
    (authApi.me as ReturnType<typeof vi.fn>).mockResolvedValue({
      username: 'user', email: 'u@e.com', role: 'USER', customer: { id: '1', name: 'C' },
    });
    (totpApi.status as ReturnType<typeof vi.fn>).mockResolvedValue({ enabled: false });
    (webauthnApi.listCredentials as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (webauthnApi.registerBegin as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error('Registration failed')
    );

    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Add Security Key' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Add Security Key' }));
    fireEvent.change(screen.getByPlaceholderText('e.g., YubiKey, Touch ID'), {
      target: { value: 'My Key' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Add Key' }));

    await waitFor(() => {
      expect(screen.getByText('Registration failed')).toBeInTheDocument();
    });
  });
});
