import { useEffect, useState } from "react";

import { getWorkerDashboard } from "../api/workerApi";

import ProfileCard from "./components/ProfileCard";
import StabilityCard from "./components/StabilityCard";
import IncomeSummary from "./components/IncomeSummary";
import IncomeChart from "./components/IncomeChart";
import EmergencyFund from "./components/EmergencyFund";
import RecommendationCard from "./components/RecommendationCard";

function WorkerDashboard({ workerId }) {
  const [workerData, setWorkerData] = useState(null);

  useEffect(() => {
    async function loadWorkerData() {
      const data = await getWorkerDashboard(workerId);

      setWorkerData(data);
    }

    loadWorkerData();
  }, [workerId]);

  if (!workerData) {
    return (
      <main className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-slate-600">
          Loading financial information...
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="max-w-5xl mx-auto px-4 py-5 sm:px-6 sm:py-8">

        {/* Dashboard Header */}
        <div className="mb-6 sm:mb-8">
          <p className="text-sm font-semibold text-blue-600">
            Worker Dashboard
          </p>

          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 mt-1">
            Your Financial Safety
          </h1>

          <p className="text-sm sm:text-base text-slate-500 mt-2 max-w-xl">
            Simple insights to help you manage your income and savings.
          </p>
        </div>

        {/* Worker Profile */}
        <section className="mb-4 sm:mb-5 bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5">
          <ProfileCard
            name={workerData.name}
            role={workerData.role}
          />
        </section>

        {/* Stability + Income */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5">

          {/* Stability Score */}
          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5">
            <StabilityCard
              score={workerData.stabilityScore}
            />
          </section>

          {/* Weekly Income */}
          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5">
            <IncomeSummary
              weeklyIncome={workerData.weeklyIncome}
              incomeChange={workerData.incomeChange}
            />
          </section>

        </div>

        {/* Income Trend */}
        <section className="mt-4 sm:mt-5 bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5">
          <IncomeChart
            data={workerData.incomeHistory}
          />
        </section>

        {/* Emergency Fund */}
        <section className="mt-4 sm:mt-5 bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5">
          <EmergencyFund
            current={workerData.emergencyFund}
            target={workerData.emergencyTarget}
          />
        </section>

        {/* Recommendation */}
        <section className="mt-4 sm:mt-5 bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5">
          <RecommendationCard
            score={workerData.stabilityScore}
          />
        </section>

      </div>
    </main>
  );
}

export default WorkerDashboard;