import { useState } from "react";

import Navigation from "./components/Navigation";
import WorkerDashboard from "./worker-dashboard/WorkerDashboard";
import FlowShieldWidget from "./sdk-widget/FlowShieldWidget";

function App() {
  const [currentView, setCurrentView] = useState("widget");

  return (
    <div>
      <Navigation
        currentView={currentView}
        onChange={setCurrentView}
      />

      {currentView === "worker" && (
        <WorkerDashboard workerId={1} />
      )}

      {currentView === "widget" && (
        <FlowShieldWidget workerId={1} />
      )}
    </div>
  );
}

export default App;