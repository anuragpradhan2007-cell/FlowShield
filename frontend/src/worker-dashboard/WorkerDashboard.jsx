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
    return (
      <div className="flex items-center justify-center py-10">
        <p className="text-sm text-slate-600">
          Loading financial information...
        </p>
      </div>
    );
  }

  return (
    <main className="bg-slate-50">

      <div className="px-4 py-5">

        {/* Dashboard Heading */}
        <div className="mb-5">

          <p className="text-sm font-semibold text-blue-600">
            Financial Overview
          </p>

          <h1 className="text-xl font-bold text-slate-900 mt-1">
            Your Financial Safety
          </h1>

          <p className="text-sm text-slate-500 mt-1">
            Simple insights to help you manage your earnings and savings.
          </p>

        </div>

        {/* Profile */}
        <section className="mb-4 bg-white rounded-2xl border border-slate-200 shadow-sm p-4">

          <ProfileCard
            name={workerData.name}
            role={workerData.role}
          />

        </section>

        {/* Stability + Income */}
        <div className="grid grid-cols-1 gap-4">

          {/* Stability Score */}
          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4">

            <StabilityCard
              score={workerData.stabilityScore}
            />

          </section>

          {/* Weekly Income */}
          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4">

            <IncomeSummary
              weeklyIncome={workerData.weeklyIncome}
              incomeChange={workerData.incomeChange}
            />

          </section>

        </div>

        {/* Income Chart */}
        <section className="mt-4 bg-white rounded-2xl border border-slate-200 shadow-sm p-4">

          <IncomeChart
            data={workerData.incomeHistory}
          />

        </section>

        {/* Emergency Fund */}
        <section className="mt-4 bg-white rounded-2xl border border-slate-200 shadow-sm p-4">

          <EmergencyFund
            current={workerData.emergencyFund}
            target={workerData.emergencyTarget}
          />

        </section>

        {/* Recommendation */}
        <section className="mt-4 bg-white rounded-2xl border border-slate-200 shadow-sm p-4">

          <RecommendationCard
            score={workerData.stabilityScore}
          />

        </section>

      </div>

    </main>
  );
}

export default WorkerDashboard;