import React, { useEffect, useState } from 'react';
import { getPartnerProfile, loginAsPartner } from '../../services/partner-sdk-service';

export const PartnerDashboard = () => {
  const [partnerToken, setPartnerToken] = useState(null);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState(null);
  
  const [partner, setPartner] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!partnerToken) {
      setPartner(null);
      return;
    }

    let isMounted = true;
    const fetchProfile = async () => {
      setIsLoading(true);
      try {
        const data = await getPartnerProfile(partnerToken);
        if (isMounted) setPartner(data);
      } catch (err) {
        if (isMounted) {
          console.error("Failed to fetch profile", err);
          setPartnerToken(null); // Invalid token
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    fetchProfile();
    return () => { isMounted = false; };
  }, [partnerToken]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError(null);

    try {
      const result = await loginAsPartner(loginEmail, loginPassword);
      setPartnerToken(result.access_token);
      setLoginEmail('');
      setLoginPassword('');
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  const handleLogout = () => {
    setPartnerToken(null);
  };

  if (!partnerToken) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="bg-white rounded-lg shadow p-8 max-w-md w-full space-y-6 border border-slate-200">
          <h1 className="text-2xl font-bold">Partner Login</h1>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Email</label>
              <input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-4 py-2 mt-1 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Password</label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-4 py-2 mt-1 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                required
              />
            </div>

            {loginError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {loginError}
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (isLoading) return <div className="p-6 text-slate-600">Loading profile...</div>;
  if (!partner) return <div className="p-6 text-red-600">Failed to load partner profile</div>;

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center bg-white p-6 rounded-lg shadow-sm border border-slate-200">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">{partner.name}</h1>
          <p className="text-slate-600">{partner.email}</p>
        </div>
        <button
          onClick={handleLogout}
          className="bg-slate-100 text-slate-700 px-4 py-2 rounded-lg hover:bg-slate-200 font-medium transition"
        >
          Logout
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
          <p className="text-sm font-medium text-slate-500 mb-1">Commission Rate</p>
          <p className="text-2xl font-bold text-slate-900">{partner.commission_rate}%</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
          <p className="text-sm font-medium text-slate-500 mb-1">Total Earnings</p>
          <p className="text-2xl font-bold text-green-600">${partner.total_earnings.toFixed(2)}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
          <p className="text-sm font-medium text-slate-500 mb-1">Total Workers Enrolled</p>
          <p className="text-2xl font-bold text-blue-600">{partner.total_workers}</p>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
        <h2 className="text-xl font-bold text-slate-900 mb-4">API Configuration</h2>
        <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 overflow-hidden">
          <p className="text-sm font-medium text-slate-500 mb-1">Live API Key</p>
          <code className="block bg-slate-100 p-2 rounded text-sm text-slate-800 break-all">
            {partner.api_key}
          </code>
          <p className="text-xs text-slate-500 mt-2">Only the last 10 characters are shown for security.</p>
        </div>
      </div>
    </div>
  );
};
export default PartnerDashboard;
