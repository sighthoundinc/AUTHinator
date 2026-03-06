import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startRegistration } from '@simplewebauthn/browser';
import { authApi, totpApi, webauthnApi } from '../api/client';
import { getApiErrorMessage, User, WebAuthnCredential } from '../api/types';

const Profile: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // TOTP state
  const [totpEnabled, setTotpEnabled] = useState(false);
  const [showTotpSetup, setShowTotpSetup] = useState(false);
  const [showTotpDisable, setShowTotpDisable] = useState(false);
  const [totpQrCode, setTotpQrCode] = useState('');
  const [totpToken, setTotpToken] = useState('');
  const [totpDisableToken, setTotpDisableToken] = useState('');
  const [totpLoading, setTotpLoading] = useState(false);

  // WebAuthn state
  const [webauthnCredentials, setWebauthnCredentials] = useState<WebAuthnCredential[]>([]);
  const [showWebauthnAdd, setShowWebauthnAdd] = useState(false);
  const [webauthnName, setWebauthnName] = useState('');
  const [webauthnLoading, setWebauthnLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/login');
      return;
    }

    const loadData = async () => {
      try {
        const [userData, totpStatus, credentials] = await Promise.all([
          authApi.me(),
          totpApi.status().catch(() => ({ enabled: false })),
          webauthnApi.listCredentials().catch(() => []),
        ]);
        setUser(userData);
        setTotpEnabled(totpStatus.enabled);
        setWebauthnCredentials(credentials);
      } catch (err: unknown) {
        if (
          typeof err === 'object' && err !== null &&
          'response' in err &&
          (err as { response?: { status?: number } }).response?.status === 401
        ) {
          localStorage.removeItem('auth_token');
          navigate('/login');
        } else {
          setError(getApiErrorMessage(err, 'Failed to load profile'));
        }
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [navigate]);

  // ─── TOTP handlers ──────────────────────────────────────────────────

  const handleTotpSetup = async () => {
    setTotpLoading(true);
    setError('');
    setMessage('');
    try {
      const data = await totpApi.setup();
      setTotpQrCode(data.qr_code);
      setShowTotpSetup(true);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to initialize TOTP setup'));
    }
    setTotpLoading(false);
  };

  const handleTotpConfirm = async () => {
    if (!totpToken) {
      setError('Please enter the 6-digit code from your authenticator app');
      return;
    }
    setTotpLoading(true);
    setError('');
    try {
      await totpApi.confirm(totpToken);
      setTotpEnabled(true);
      setShowTotpSetup(false);
      setTotpToken('');
      setMessage('Two-factor authentication enabled successfully');
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Invalid verification code'));
    }
    setTotpLoading(false);
  };

  const handleTotpDisable = async () => {
    if (!totpDisableToken) {
      setError('Please enter the 6-digit code from your authenticator app');
      return;
    }
    setTotpLoading(true);
    setError('');
    setMessage('');
    try {
      await totpApi.disable(totpDisableToken);
      setTotpEnabled(false);
      setShowTotpDisable(false);
      setTotpDisableToken('');
      setMessage('Two-factor authentication disabled successfully');
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to disable TOTP'));
    }
    setTotpLoading(false);
  };

  // ─── WebAuthn handlers ──────────────────────────────────────────────

  const handleWebauthnAdd = async () => {
    if (!webauthnName.trim()) {
      setError('Please enter a name for this security key');
      return;
    }
    setWebauthnLoading(true);
    setError('');
    setMessage('');
    try {
      const { options } = await webauthnApi.registerBegin(webauthnName);
      const credential = await startRegistration(options);
      await webauthnApi.registerComplete(credential);
      const updatedList = await webauthnApi.listCredentials();
      setWebauthnCredentials(updatedList);
      setShowWebauthnAdd(false);
      setWebauthnName('');
      setMessage('Security key added successfully');
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to add security key'));
    }
    setWebauthnLoading(false);
  };

  const handleWebauthnDelete = async (credentialId: number) => {
    if (!confirm('Are you sure you want to remove this security key?')) return;
    try {
      await webauthnApi.deleteCredential(credentialId);
      setWebauthnCredentials(prev => prev.filter(c => c.id !== credentialId));
      setMessage('Security key removed successfully');
    } catch {
      setError('Failed to remove security key');
    }
  };

  // ─── Render ─────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/')}
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              ← Back
            </button>
            <h1 className="text-2xl font-bold text-gray-900">🔐 Security Settings</h1>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {message && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">{message}</p>
          </div>
        )}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Profile Info */}
        <section className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Account Information</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-500">Username</span>
              <p className="mt-1 text-gray-900">{user?.username}</p>
            </div>
            <div>
              <span className="font-medium text-gray-500">Email</span>
              <p className="mt-1 text-gray-900">{user?.email}</p>
            </div>
            <div>
              <span className="font-medium text-gray-500">Role</span>
              <p className="mt-1 text-gray-900">{user?.role}</p>
            </div>
            <div>
              <span className="font-medium text-gray-500">Organization</span>
              <p className="mt-1 text-gray-900">{user?.customer?.name ?? 'N/A'}</p>
            </div>
          </div>
        </section>

        {/* TOTP Section */}
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Two-Factor Authentication</h2>
              <p className="text-sm text-gray-500 mt-1">
                Add an extra layer of security with an authenticator app (Google Authenticator, Authy, etc.)
              </p>
            </div>
            {!totpEnabled && !showTotpSetup && (
              <button
                onClick={handleTotpSetup}
                disabled={totpLoading}
                className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {totpLoading ? 'Loading...' : 'Enable 2FA'}
              </button>
            )}
            {totpEnabled && !showTotpDisable && (
              <div className="flex items-center space-x-3">
                <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-lg">
                  ✓ Enabled
                </span>
                <button
                  onClick={() => setShowTotpDisable(true)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Disable 2FA
                </button>
              </div>
            )}
          </div>

          {showTotpSetup && (
            <div className="bg-gray-50 rounded-lg p-5 mt-4">
              <h3 className="font-semibold text-gray-900 mb-2">Scan QR Code</h3>
              <p className="text-sm text-gray-600 mb-4">
                Scan this QR code with your authenticator app, then enter the 6-digit code to verify.
              </p>
              {totpQrCode && (
                <div className="flex justify-center py-4 bg-white rounded mb-4">
                  <img src={totpQrCode} alt="TOTP QR Code" className="max-w-[200px]" />
                </div>
              )}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Verification Code</label>
                <input
                  type="text"
                  value={totpToken}
                  onChange={e => setTotpToken(e.target.value)}
                  placeholder="Enter 6-digit code"
                  maxLength={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => { setShowTotpSetup(false); setTotpToken(''); }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleTotpConfirm}
                  disabled={totpLoading}
                  className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  {totpLoading ? 'Verifying...' : 'Verify & Enable'}
                </button>
              </div>
            </div>
          )}

          {showTotpDisable && (
            <div className="bg-gray-50 rounded-lg p-5 mt-4">
              <h3 className="font-semibold text-gray-900 mb-2">Disable Two-Factor Authentication</h3>
              <p className="text-sm text-gray-600 mb-4">
                Enter a 6-digit code from your authenticator app to confirm disabling 2FA.
              </p>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Verification Code</label>
                <input
                  type="text"
                  value={totpDisableToken}
                  onChange={e => setTotpDisableToken(e.target.value)}
                  placeholder="Enter 6-digit code"
                  maxLength={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => { setShowTotpDisable(false); setTotpDisableToken(''); }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleTotpDisable}
                  disabled={totpLoading}
                  className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {totpLoading ? 'Disabling...' : 'Disable 2FA'}
                </button>
              </div>
            </div>
          )}
        </section>

        {/* WebAuthn Section */}
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Security Keys (WebAuthn)</h2>
              <p className="text-sm text-gray-500 mt-1">
                Use hardware security keys or biometric authentication for passwordless login
              </p>
            </div>
            <button
              onClick={() => setShowWebauthnAdd(true)}
              disabled={showWebauthnAdd}
              className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              Add Security Key
            </button>
          </div>

          {webauthnCredentials.length > 0 && (
            <div className="space-y-3 mt-4">
              {webauthnCredentials.map(cred => (
                <div key={cred.id} className="flex justify-between items-center p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div>
                    <p className="font-medium text-gray-900">🔑 {cred.name}</p>
                    <p className="text-xs text-gray-500">Added: {new Date(cred.created_at).toLocaleDateString()}</p>
                  </div>
                  <button
                    onClick={() => handleWebauthnDelete(cred.id)}
                    className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          {showWebauthnAdd && (
            <div className="bg-gray-50 rounded-lg p-5 mt-4">
              <h3 className="font-semibold text-gray-900 mb-2">Add Security Key</h3>
              <p className="text-sm text-gray-600 mb-4">
                Give your security key a name, then follow your browser's prompts.
              </p>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Security Key Name</label>
                <input
                  type="text"
                  value={webauthnName}
                  onChange={e => setWebauthnName(e.target.value)}
                  placeholder="e.g., YubiKey, Touch ID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => { setShowWebauthnAdd(false); setWebauthnName(''); }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleWebauthnAdd}
                  disabled={webauthnLoading}
                  className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  {webauthnLoading ? 'Adding...' : 'Add Key'}
                </button>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default Profile;
