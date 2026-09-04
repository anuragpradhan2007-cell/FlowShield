
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getWorkerDashboard(token) {
  try {
    const headers = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(
      `${API_URL}/api/v1/dashboard/worker/me`,
      { headers }
    );

    if (!response.ok) {
      throw new Error("Failed to fetch worker dashboard");
    }

    const data = await response.json();

    return data;
  } catch (error) {
    console.error("Failed to fetch worker dashboard:", error.message);
    throw error;
  }
}

export async function addEarning(token, amount) {
  try {
    const headers = {
      "Content-Type": "application/json"
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(
      `${API_URL}/api/v1/dashboard/worker/add-earning`,
      { 
        method: "POST", 
        headers,
        body: JSON.stringify({ amount })
      }
    );

    if (!response.ok) {
      throw new Error("Failed to add earning");
    }
    
    return await response.json();
  } catch (error) {
    console.error("Failed to add earning:", error.message);
    throw error;
  }
}