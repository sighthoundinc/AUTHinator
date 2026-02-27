import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  };
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
    },
  };
});

describe('client module', () => {
  beforeEach(() => {
    vi.resetModules();
    localStorage.clear();
  });

  it('should create axios instance with correct config', async () => {
    await import('./client');
    expect(axios.create).toHaveBeenCalledWith({
      baseURL: 'http://localhost:8001/api',
      headers: { 'Content-Type': 'application/json' },
    });
  });

  it('should register a request interceptor', async () => {
    const mod = await import('./client');
    const instance = mod.default;
    expect(instance.interceptors.request.use).toHaveBeenCalled();
  });

  it('request interceptor should add auth token when present', async () => {
    localStorage.setItem('auth_token', 'test-token-123');
    vi.resetModules();
    await import('./client');

    const mockInstance = (axios.create as ReturnType<typeof vi.fn>).mock.results[0]?.value;
    const interceptorFn = mockInstance.interceptors.request.use.mock.calls[0]?.[0];

    if (interceptorFn) {
      const config = { headers: {} as Record<string, string> };
      const result = interceptorFn(config);
      expect(result.headers.Authorization).toBe('Bearer test-token-123');
    }
  });

  it('request interceptor should not add header when no token', async () => {
    vi.resetModules();
    await import('./client');

    const mockInstance = (axios.create as ReturnType<typeof vi.fn>).mock.results[0]?.value;
    const interceptorFn = mockInstance.interceptors.request.use.mock.calls[0]?.[0];

    if (interceptorFn) {
      const config = { headers: {} as Record<string, string> };
      const result = interceptorFn(config);
      expect(result.headers.Authorization).toBeUndefined();
    }
  });

  it('authApi.login should post credentials and return data', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.post as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { access: 'a-token', refresh: 'r-token' },
    });

    const result = await mod.authApi.login('user', 'pass');
    expect(instance.post).toHaveBeenCalledWith('/auth/login/', {
      username: 'user',
      password: 'pass',
    });
    expect(result).toEqual({ access: 'a-token', refresh: 'r-token' });
  });

  it('authApi.me should get current user', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    const mockUser = { id: '1', username: 'test' };
    (instance.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockUser });

    const result = await mod.authApi.me();
    expect(instance.get).toHaveBeenCalledWith('/auth/me/');
    expect(result).toEqual(mockUser);
  });

  it('authApi.logout should post refresh token', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.post as ReturnType<typeof vi.fn>).mockResolvedValue({});

    await mod.authApi.logout('refresh-123');
    expect(instance.post).toHaveBeenCalledWith('/auth/logout/', { refresh: 'refresh-123' });
  });

  it('servicesApi.list should get services', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    const mockServices = [{ id: 1, name: 'RMAinator' }];
    (instance.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockServices });

    const result = await mod.servicesApi.list();
    expect(instance.get).toHaveBeenCalledWith('/services/');
    expect(result).toEqual(mockServices);
  });

  // ─── TOTP API tests ─────────────────────────────────────────────────

  it('totpApi.status should get TOTP status', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { enabled: true } });

    const result = await mod.totpApi.status();
    expect(instance.get).toHaveBeenCalledWith('/auth/totp/status/');
    expect(result).toEqual({ enabled: true });
  });

  it('totpApi.setup should post and return QR data', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.post as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { qr_code: 'data:image/png;base64,QR', secret: 'SECRET' },
    });

    const result = await mod.totpApi.setup();
    expect(instance.post).toHaveBeenCalledWith('/auth/totp/setup/');
    expect(result.secret).toBe('SECRET');
  });

  it('totpApi.confirm should post token', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.post as ReturnType<typeof vi.fn>).mockResolvedValue({});

    await mod.totpApi.confirm('123456');
    expect(instance.post).toHaveBeenCalledWith('/auth/totp/confirm/', { token: '123456' });
  });

  it('totpApi.disable should post token', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.post as ReturnType<typeof vi.fn>).mockResolvedValue({});

    await mod.totpApi.disable('654321');
    expect(instance.post).toHaveBeenCalledWith('/auth/totp/disable/', { token: '654321' });
  });

  // ─── WebAuthn API tests ─────────────────────────────────────────────

  it('webauthnApi.listCredentials should get credentials', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    const creds = [{ id: 1, name: 'YubiKey', created_at: '2025-01-01' }];
    (instance.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: creds });

    const result = await mod.webauthnApi.listCredentials();
    expect(instance.get).toHaveBeenCalledWith('/auth/webauthn/credentials/');
    expect(result).toEqual(creds);
  });

  it('webauthnApi.registerBegin should post name', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { options: {} } });

    const result = await mod.webauthnApi.registerBegin('My Key');
    expect(instance.post).toHaveBeenCalledWith('/auth/webauthn/register/begin/', { name: 'My Key' });
    expect(result).toEqual({ options: {} });
  });

  it('webauthnApi.registerComplete should post credential', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { detail: 'ok' } });

    const cred = { id: 'test', response: {} };
    const result = await mod.webauthnApi.registerComplete(cred);
    expect(instance.post).toHaveBeenCalledWith('/auth/webauthn/register/complete/', cred);
    expect(result).toEqual({ detail: 'ok' });
  });

  it('webauthnApi.deleteCredential should delete by id', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    const mockDelete = vi.fn().mockResolvedValue({});
    (instance as Record<string, unknown>).delete = mockDelete;

    await mod.webauthnApi.deleteCredential(42);
    expect(mockDelete).toHaveBeenCalledWith('/auth/webauthn/credentials/42/');
  });

  // ─── MFA Login API tests ──────────────────────────────────────────────

  it('mfaApi.totpVerify should post mfa_token and code', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.post as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { access: 'a-tok', refresh: 'r-tok' },
    });

    const result = await mod.mfaApi.totpVerify('mfa-123', '654321');
    expect(instance.post).toHaveBeenCalledWith('/auth/mfa/totp-verify/', {
      mfa_token: 'mfa-123',
      code: '654321',
    });
    expect(result).toEqual({ access: 'a-tok', refresh: 'r-tok' });
  });

  it('mfaApi.webauthnBegin should post mfa_token', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.post as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { options: { challenge: 'abc' } },
    });

    const result = await mod.mfaApi.webauthnBegin('mfa-123');
    expect(instance.post).toHaveBeenCalledWith('/auth/mfa/webauthn-begin/', {
      mfa_token: 'mfa-123',
    });
    expect(result).toEqual({ options: { challenge: 'abc' } });
  });

  it('mfaApi.webauthnComplete should post mfa_token and assertion', async () => {
    vi.resetModules();
    const mod = await import('./client');
    const instance = mod.default;
    (instance.post as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { access: 'a-tok', refresh: 'r-tok' },
    });

    const assertion = { id: 'cred-id', rawId: 'cred-id', type: 'public-key' };
    const result = await mod.mfaApi.webauthnComplete('mfa-123', assertion);
    expect(instance.post).toHaveBeenCalledWith('/auth/mfa/webauthn-complete/', {
      mfa_token: 'mfa-123',
      ...assertion,
    });
    expect(result).toEqual({ access: 'a-tok', refresh: 'r-tok' });
  });
});
