import { useEffect, useState } from "react";
import { WorkerSDKModal } from "../components/SDK/WorkerSDKModal";
import { getWorkerDashboard, addEarning } from "../api/workerApi";

import ProfileCard from "./components/ProfileCard";
import StabilityCard from "./components/StabilityCard";
import IncomeSummary from "./components/IncomeSummary";
import IncomeChart from "./components/IncomeChart";
import EmergencyFund from "./components/EmergencyFund";
import RecommendationCard from "./components/RecommendationCard";

function WorkerDashboard({ token }) {
  const [workerData, setWorkerData] = useState(null);
  const [isSDKModalOpen, setIsSDKModalOpen] = useState(false);
  const [error, setError] = useState(null);
  const [isAddingEarning, setIsAddingEarning] = useState(false);
  const [earningAmount, setEarningAmount] = useState("");

  useEffect(() => {
    async function loadWorkerData() {
      try {
        const data = await getWorkerDashboard(token);
        setWorkerData(data);
      } catch (err) {
        setError(err.message || "Failed to load financial data");
      }
    }

    if (token) {
      loadWorkerData();
    }
  }, [token]);

  if (error) {
    return (
      <div className="flex items-center justify-center py-10">
        <p className="text-sm text-red-600">Error: {error}</p>
      </div>
    );
  }

  if (!workerData) {
    return (
      <div className="flex items-center justify-center py-10">
        <p className="text-sm text-slate-600">
          Loading financial information...
        </p>
      </div>
    );
  }

  const handleAddEarning = async (e) => {
    e.preventDefault();
    if (!earningAmount || isNaN(earningAmount)) return;

    setIsAddingEarning(true);
    try {
      await addEarning(token, parseFloat(earningAmount));
      const data = await getWorkerDashboard(token);
      setWorkerData(data);
      setEarningAmount("");
    } catch (err) {
      alert("Failed to add earning");
    } finally {
      setIsAddingEarning(false);
    }
  };

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

          <form onSubmit={handleAddEarning} className="mt-4 flex gap-2">
            <input
              type="number"
              step="0.01"
              value={earningAmount}
              onChange={(e) => setEarningAmount(e.target.value)}
              placeholder="Earning Amount ($)"
              className="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              required
            />
            <button
              type="submit"
              disabled={isAddingEarning}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50"
            >
              {isAddingEarning ? "Adding..." : "Add Earning"}
            </button>
          </form>
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

        {/* Partner Services */}
        <section className="mt-4 bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
          <h2 className="text-xl font-bold mb-2">Financial Protection</h2>
          <p className="text-sm text-slate-600 mb-4">
            Access emergency funds, micro-credit, and savings tools from our partners.
          </p>
          <button
            onClick={() => setIsSDKModalOpen(true)}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Access Partner Services
          </button>
        </section>

      </div>

      <WorkerSDKModal 
        isOpen={isSDKModalOpen}
        onClose={() => setIsSDKModalOpen(false)}
        workerToken={token}
      />

    </main>
  );
}

export default WorkerDashboard;