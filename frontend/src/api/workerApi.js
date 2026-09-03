
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