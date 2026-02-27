import axios from 'axios';
import { LoginResult, LoginResponse, User, Service, TotpStatusResponse, TotpSetupResponse, WebAuthnCredential } from './types';

const API_BASE = 'http://localhost:8001/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResult> => {
    const response = await apiClient.post<LoginResult>('/auth/login/', {
      username,
      password,
    });
    return response.data;
  },

  me: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me/');
    return response.data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post('/auth/logout/', { refresh: refreshToken });
  },
};

export const servicesApi = {
  list: async (): Promise<Service[]> => {
    const response = await apiClient.get<Service[]>('/services/');
    return response.data;
  },
};

export const totpApi = {
  status: async (): Promise<TotpStatusResponse> => {
    const response = await apiClient.get<TotpStatusResponse>('/auth/totp/status/');
    return response.data;
  },
  setup: async (): Promise<TotpSetupResponse> => {
    const response = await apiClient.post<TotpSetupResponse>('/auth/totp/setup/');
    return response.data;
  },
  confirm: async (token: string): Promise<void> => {
    await apiClient.post('/auth/totp/confirm/', { token });
  },
  disable: async (token: string): Promise<void> => {
    await apiClient.post('/auth/totp/disable/', { token });
  },
};

export const mfaApi = {
  totpVerify: async (mfaToken: string, code: string): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/mfa/totp-verify/', {
      mfa_token: mfaToken,
      code,
    });
    return response.data;
  },
  webauthnBegin: async (mfaToken: string) => {
    const response = await apiClient.post('/auth/mfa/webauthn-begin/', {
      mfa_token: mfaToken,
    });
    return response.data;
  },
  webauthnComplete: async (mfaToken: string, assertion: unknown): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/mfa/webauthn-complete/', {
      mfa_token: mfaToken,
      ...assertion as Record<string, unknown>,
    });
    return response.data;
  },
};

export const webauthnApi = {
  listCredentials: async (): Promise<WebAuthnCredential[]> => {
    const response = await apiClient.get<WebAuthnCredential[]>('/auth/webauthn/credentials/');
    return response.data;
  },
  registerBegin: async (name: string) => {
    const response = await apiClient.post('/auth/webauthn/register/begin/', { name });
    return response.data;
  },
  registerComplete: async (credential: unknown) => {
    const response = await apiClient.post('/auth/webauthn/register/complete/', credential);
    return response.data;
  },
  deleteCredential: async (id: number): Promise<void> => {
    await apiClient.delete(`/auth/webauthn/credentials/${id}/`);
  },
};

export default apiClient;
