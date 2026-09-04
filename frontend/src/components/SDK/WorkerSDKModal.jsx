import React, { useEffect, useState } from 'react';
import { getSDKTokenForWorker } from '../../services/partner-sdk-service';

export const WorkerSDKModal = ({ isOpen, onClose, workerToken }) => {
  const [sdkToken, setSDKToken] = useState(null);
  const [tokenPayload, setTokenPayload] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !workerToken) return;

    const fetchSDKToken = async () => {
      setLoading(true);
      setError(null);

      try {
        // Get real SDK token from backend
        const response = await getSDKTokenForWorker(workerToken);
        setSDKToken(response.sdk_token);
        
        // Decode token payload
        try {
          const payloadBase64 = response.sdk_token.split('.')[0];
          const payloadStr = atob(payloadBase64);
          const payload = JSON.parse(payloadStr);
          setTokenPayload(payload);
        } catch(e) {
          console.error("Failed to parse token payload", e);
        }
        
        // In a real scenario, you would initialize the partner's SDK here
        console.log(`SDK Token received from ${response.partner_name}`);
        console.log(`Token expires at: ${response.expires_at}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get SDK token');
        console.error('SDK token error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSDKToken();
  }, [isOpen, workerToken]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full space-y-4">
        <h2 className="text-2xl font-bold">Partner Services</h2>

        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin">⚙️</div>
            <p className="text-gray-600 mt-2">Loading partner services...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            Error: {error}
          </div>
        )}

        {sdkToken && !loading && (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
              ✓ Connected to {tokenPayload?.partner_name || 'partner services'}
            </div>
            
            {tokenPayload && (
              <div className="bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded text-sm space-y-2">
                <p className="font-bold border-b border-blue-200 pb-2 mb-2">Verified FlowShield Profile Shared:</p>
                <div className="flex justify-between">
                  <span>ML Risk Tier:</span>
                  <span className="font-semibold">{tokenPayload.risk_tier}</span>
                </div>
                <div className="flex justify-between">
                  <span>Stability Score:</span>
                  <span className="font-semibold">{tokenPayload.risk_score} / 100</span>
                </div>
                <div className="flex justify-between">
                  <span>Emergency Fund:</span>
                  <span className="font-semibold">${tokenPayload.flowshield_balance?.toFixed(2)}</span>
                </div>
              </div>
            )}
            
            <div className="bg-gray-50 p-4 rounded border border-gray-200 overflow-hidden">
              <p className="text-xs text-gray-600 mb-2">SDK Token (for reference):</p>
              <code className="text-xs break-all block">{sdkToken.substring(0, 50)}...</code>
            </div>

            <p className="text-sm text-gray-600">
              The partner's SDK uses your FlowShield profile to instantly unlock micro-credit and emergency funds securely.
            </p>
          </div>
        )}

        <button
          onClick={onClose}
          className="w-full bg-orange-500 text-white py-2 rounded font-semibold hover:bg-orange-600"
        >
          {sdkToken && !error ? 'Close' : 'Cancel'}
        </button>
      </div>
    </div>
  );
};
