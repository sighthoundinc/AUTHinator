import { describe, it, expect } from 'vitest';
import { getAxiosErrorData, getApiErrorMessage, isMfaRequired } from './types';

describe('getAxiosErrorData', () => {
  it('should return response data from an axios-like error', () => {
    const err = { response: { data: { detail: 'Not found' } } };
    expect(getAxiosErrorData(err)).toEqual({ detail: 'Not found' });
  });

  it('should return undefined for non-object error', () => {
    expect(getAxiosErrorData('string error')).toBeUndefined();
    expect(getAxiosErrorData(null)).toBeUndefined();
    expect(getAxiosErrorData(undefined)).toBeUndefined();
    expect(getAxiosErrorData(42)).toBeUndefined();
  });

  it('should return undefined when error has no response', () => {
    expect(getAxiosErrorData({})).toBeUndefined();
    expect(getAxiosErrorData({ message: 'fail' })).toBeUndefined();
  });

  it('should return undefined when response has no data', () => {
    expect(getAxiosErrorData({ response: {} })).toBeUndefined();
    expect(getAxiosErrorData({ response: { data: null } })).toBeUndefined();
    expect(getAxiosErrorData({ response: { data: 'string' } })).toBeUndefined();
  });

  it('should return undefined when response is not an object', () => {
    expect(getAxiosErrorData({ response: 'not-object' })).toBeUndefined();
  });
});

describe('getApiErrorMessage', () => {
  it('should extract detail from axios error data', () => {
    const err = { response: { data: { detail: 'Token expired' } } };
    expect(getApiErrorMessage(err, 'fallback')).toBe('Token expired');
  });

  it('should extract error from axios error data', () => {
    const err = { response: { data: { error: 'Invalid credentials' } } };
    expect(getApiErrorMessage(err, 'fallback')).toBe('Invalid credentials');
  });

  it('should prefer detail over error', () => {
    const err = { response: { data: { detail: 'detail msg', error: 'error msg' } } };
    expect(getApiErrorMessage(err, 'fallback')).toBe('detail msg');
  });

  it('should use Error.message when no response data', () => {
    expect(getApiErrorMessage(new Error('network error'), 'fallback')).toBe('network error');
  });

  it('should return fallback for unknown error types', () => {
    expect(getApiErrorMessage('string', 'fallback')).toBe('fallback');
    expect(getApiErrorMessage(null, 'fallback')).toBe('fallback');
    expect(getApiErrorMessage(42, 'fallback')).toBe('fallback');
    expect(getApiErrorMessage({}, 'fallback')).toBe('fallback');
  });
});

describe('isMfaRequired', () => {
  it('should return true for MFA required response', () => {
    const result = { mfa_required: true as const, mfa_token: 'tok', mfa_methods: ['totp'] };
    expect(isMfaRequired(result)).toBe(true);
  });

  it('should return false for normal login response', () => {
    const result = { access: 'access-tok', refresh: 'refresh-tok' };
    expect(isMfaRequired(result)).toBe(false);
  });
});
