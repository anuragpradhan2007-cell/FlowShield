import { useState, useEffect } from "react";

import Navigation from "./components/Navigation";
import WorkerDashboard from "./worker-dashboard/WorkerDashboard";
import PartnerDashboard from "./partner-dashboard/PartnerDashboard";
import FlowShieldWidget from "./sdk-widget/FlowShieldWidget";

function App() {
  const [currentView, setCurrentView] = useState("widget");
  const [sdkToken, setSdkToken] = useState(null);

  useEffect(() => {
    // Simulate Host App (e.g., Swiggy) fetching an SDK token for the driver
    const fetchToken = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/v1/auth/sdk/token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            partner_api_key: "mock-partner-key-123",
            host_worker_id: "swiggy-driver-987"
          })
        });
        const data = await response.json();
        setSdkToken(data.access_token);
      } catch (err) {
        console.error("Failed to fetch SDK token:", err);
      }
    };
    fetchToken();
  }, []);

  return (
    <div>
      <Navigation
        currentView={currentView}
        onChange={setCurrentView}
      />

      {currentView === "worker" && (
        <WorkerDashboard workerId={1} />
      )}

      {currentView === "partner" && (
        <PartnerDashboard />
      )}

      {currentView === "widget" && (
        <FlowShieldWidget workerId={1} token={sdkToken} />
      )}
    </div>
  );
}

export default App;