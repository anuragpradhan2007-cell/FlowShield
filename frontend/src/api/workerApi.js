import workerData from "../worker-dashboard/workerData";

const API_URL = "http://localhost:8000";

export async function getWorkerDashboard(workerId, token) {
  let profileData = {};
  
  try {
    if (token) {
      // Fetch real identity from our B2B Auth backend
      const profileResponse = await fetch(`${API_URL}/api/v1/me`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (profileResponse.ok) {
        const profile = await profileResponse.json();
        profileData = {
          name: profile.email,
          role: profile.worker.occupation
        };
      }
    }

    // Try to fetch the full dashboard data
    const response = await fetch(`${API_URL}/dashboard/worker/${workerId}`);

    if (!response.ok) {
      throw new Error("Failed to fetch worker dashboard");
    }

    const data = await response.json();
    return { ...data, ...profileData };
  } catch (error) {
    console.log("Using demo worker data:", error.message);
    return { ...workerData, ...profileData };
  }
}