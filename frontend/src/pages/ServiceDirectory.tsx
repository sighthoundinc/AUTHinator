import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, servicesApi } from '../api/client';
import { getAxiosErrorData, User, Service } from '../api/types';

const ServiceDirectory: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    // Check for token in URL parameter (from SSO callback)
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('token');
    
    if (tokenFromUrl) {
      // Store token and clean URL
      localStorage.setItem('auth_token', tokenFromUrl);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    // Check if token exists, if not redirect to login
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/login');
      return;
    }
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [userData, servicesData] = await Promise.all([
        authApi.me(),
        servicesApi.list(),
      ]);
      setUser(userData);
      setServices(servicesData);
    } catch (err: unknown) {
      const errData = getAxiosErrorData(err);
      if (
        typeof err === 'object' && err !== null &&
        'response' in err &&
        (err as { response?: { status?: number } }).response?.status === 401
      ) {
        // Token expired or invalid, redirect to login
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        navigate('/login');
      } else {
        setError(typeof errData?.detail === 'string' ? errData.detail : 'Failed to load data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      authApi.logout(refreshToken).catch(() => {});
    }
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

  const handleOpenService = (service: Service) => {
    const token = localStorage.getItem('auth_token');
    window.location.href = `${service.ui_url}?token=${token}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">🔐 AUTHinator</h1>
              <span className="ml-4 text-sm text-gray-500">Service Directory</span>
            </div>
            
            {user && (
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{user.username}</p>
                  <p className="text-xs text-gray-500">{user.customer?.name ?? user.role}</p>
                </div>
                <button
                  onClick={() => navigate('/profile')}
                  className="px-4 py-2 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
                >
                  🔒 Security
                </button>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Your Services</h2>
          <p className="text-gray-600">Click on a service to open it</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {services.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500">No services registered yet</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {services.map((service) => (
              <div
                key={service.id}
                className="bg-white rounded-lg shadow hover:shadow-xl transition-shadow cursor-pointer"
                onClick={() => handleOpenService(service)}
              >
                <div className="p-6">
                  <div className="text-5xl mb-4">{service.icon}</div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {service.name}
                  </h3>
                  <p className="text-gray-600 mb-4">{service.description}</p>
                  <button className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors">
                    Open Service
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default ServiceDirectory;
