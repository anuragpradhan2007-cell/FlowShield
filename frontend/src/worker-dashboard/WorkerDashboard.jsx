import { useEffect, useState } from "react";

import { getWorkerDashboard } from "../api/workerApi";

import ProfileCard from "./components/ProfileCard";
import StabilityCard from "./components/StabilityCard";
import IncomeSummary from "./components/IncomeSummary";
import IncomeChart from "./components/IncomeChart";
import EmergencyFund from "./components/EmergencyFund";
import RecommendationCard from "./components/RecommendationCard";

function WorkerDashboard({ workerId, token }) {
  const [workerData, setWorkerData] = useState(null);

  useEffect(() => {
    async function loadWorkerData() {
      const data = await getWorkerDashboard(workerId, token);

      setWorkerData(data);
    }

    loadWorkerData();
  }, [workerId]);

  if (!workerData) {
    return <p>Loading financial information...</p>;
  }

  return (
    <main>
      <section>
        <ProfileCard
          name={workerData.name}
          role={workerData.role}
        />
      </section>

      <section>
        <StabilityCard
          score={workerData.stabilityScore}
        />
      </section>

      <section>
        <IncomeSummary
          weeklyIncome={workerData.weeklyIncome}
          incomeChange={workerData.incomeChange}
        />

        <IncomeChart
          data={workerData.incomeHistory}
        />
      </section>

      <section>
        <EmergencyFund
          current={workerData.emergencyFund}
          target={workerData.emergencyTarget}
        />
      </section>

      <section>
        <RecommendationCard
          score={workerData.stabilityScore}
        />
      </section>
    </main>
  );
}

export default WorkerDashboard;