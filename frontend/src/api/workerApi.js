import workerData from "../worker-dashboard/workerData";

const API_URL = "http://localhost:8000";

export async function getWorkerDashboard(workerId, token) {
  try {
    const headers = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(
      `${API_URL}/api/v1/dashboard/worker/${workerId}`,
      { headers }
    );

    if (!response.ok) {
      throw new Error("Failed to fetch worker dashboard");
    }

    const data = await response.json();

    return data;
  } catch (error) {
    console.log("Using demo worker data:", error.message);

    return workerData;
  }
}