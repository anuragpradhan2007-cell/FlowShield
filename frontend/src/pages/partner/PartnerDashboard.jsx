import React, { useEffect, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const PartnerDashboard = () => {
  const [token, setToken] = useState(null);
  const [partner, setPartner] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState('demo-partner@flowshield.local');
  const [password, setPassword] = useState('DemoPassword123!');

  const loginPartner = async (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/sdk/partner/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      if (res.ok) {
        const data = await res.json();
        setToken(data.token);
      } else {
        alert("Login failed");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    
    const fetchPartner = async () => {
      setIsLoading(true);
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/sdk/partner/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setPartner(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchPartner();
  }, [token]);

  if (!token) {
    return (
      <div className="p-6 max-w-md mx-auto mt-10 bg-white rounded-xl shadow-md">
        <h2 className="text-2xl font-bold mb-4">Partner Login</h2>
        <form onSubmit={loginPartner} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} className="mt-1 p-2 w-full border rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="mt-1 p-2 w-full border rounded-md" />
          </div>
          <button type="submit" disabled={isLoading} className="w-full bg-blue-600 text-white p-2 rounded-md font-semibold disabled:bg-blue-300">
            {isLoading ? "Logging in..." : "Login"}
          </button>
        </form>
      </div>
    );
  }

  if (isLoading || !partner) return <div className="p-10 text-center">Loading partner dashboard...</div>;

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold">Partner Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <p className="text-gray-600 text-sm font-medium">Commission Rate</p>
          <p className="text-3xl font-bold text-gray-900">{partner.commission_rate}%</p>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <p className="text-gray-600 text-sm font-medium">Total Earnings</p>
          <p className="text-3xl font-bold text-green-600">${partner.total_earnings}</p>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <p className="text-gray-600 text-sm font-medium">Active Workers</p>
          <p className="text-3xl font-bold text-blue-600">{partner.total_workers}</p>
        </div>
      </div>

      <div className="bg-slate-800 text-white p-6 rounded-lg shadow-md mt-8">
        <h3 className="text-lg font-semibold mb-2 flex items-center">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path></svg>
          Partner API Key
        </h3>
        <div className="bg-slate-900 p-3 rounded font-mono text-sm break-all text-green-400">
          {partner.api_key}
        </div>
        <p className="text-sm text-slate-400 mt-3">
          Pass this key as the <code>X-Partner-API-Key</code> header to generate cryptographically secure SDK tokens for your workers.
        </p>
      </div>
    </div>
  );
};

export default PartnerDashboard;
