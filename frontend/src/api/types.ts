export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  customer: {
    id: string;
    name: string;
  } | null;
}

export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface MfaRequiredResponse {
  mfa_required: true;
  mfa_token: string;
  mfa_methods: string[];
}

export type LoginResult = LoginResponse | MfaRequiredResponse;

export function isMfaRequired(result: LoginResult): result is MfaRequiredResponse {
  return 'mfa_required' in result && result.mfa_required === true;
}

export interface Service {
  id: number;
  name: string;
  description: string;
  ui_url: string;
  icon: string;
  is_active: boolean;
  last_registered_at: string;
}

export interface WebAuthnCredential {
  id: number;
  name: string;
  created_at: string;
}

export interface TotpSetupResponse {
  qr_code: string;
  secret: string;
}

export interface TotpStatusResponse {
  enabled: boolean;
}

/** Safely extract response data from an unknown Axios error. */
export function getAxiosErrorData(err: unknown): Record<string, unknown> | undefined {
  if (
    typeof err === 'object' &&
    err !== null &&
    'response' in err &&
    typeof (err as Record<string, unknown>).response === 'object'
  ) {
    const resp = (err as { response: { data?: unknown } }).response;
    if (typeof resp.data === 'object' && resp.data !== null) {
      return resp.data as Record<string, unknown>;
    }
  }
  return undefined;
}

/** Extract error message from an unknown catch value (typically an Axios error). */
export function getApiErrorMessage(err: unknown, fallback: string): string {
  const data = getAxiosErrorData(err);
  if (typeof data?.detail === 'string') return data.detail;
  if (typeof data?.error === 'string') return data.error;
  if (err instanceof Error) return err.message;
  return fallback;
}
