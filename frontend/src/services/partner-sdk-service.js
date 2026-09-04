// frontend/src/services/partner-sdk-service.js
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Get SDK token for authenticated worker to access partner services
 */
export async function getSDKTokenForWorker(
  workerToken,
  partnerId
) {
  const url = new URL(`${API_BASE_URL}/api/v1/sdk/worker/get-token`);
  if (partnerId) {
    url.searchParams.append('partner_id', partnerId);
  }

  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${workerToken}`
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get SDK token');
  }

  return response.json();
}

/**
 * Verify SDK token is still valid (for debugging/monitoring)
 */
export async function verifySDKToken(
  token,
  partnerApiKey
) {
  const response = await fetch(`${API_BASE_URL}/api/v1/partner/sdk/verify-token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Partner-API-Key': partnerApiKey
    },
    body: JSON.stringify({ token })
  });

  return response.ok;
}

/**
 * Partner login
 */
export async function loginAsPartner(
  email,
  password
) {
  const response = await fetch(`${API_BASE_URL}/api/v1/partner/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
}

/**
 * Get authenticated partner's profile
 */
export async function getPartnerProfile(partnerToken) {
  const response = await fetch(`${API_BASE_URL}/api/v1/partner/me`, {
    headers: { 'Authorization': `Bearer ${partnerToken}` }
  });

  if (!response.ok) {
    throw new Error('Failed to get partner profile');
  }

  return response.json();
}
