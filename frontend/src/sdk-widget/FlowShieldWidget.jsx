import { useState } from "react";
import WorkerDashboard from "../worker-dashboard/WorkerDashboard";

function FlowShieldWidget({ workerId }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Circular FlowShield Widget */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="w-20 h-20 rounded-full bg-blue-600 text-white shadow-lg flex flex-col items-center justify-center hover:bg-blue-700 active:scale-95 transition-all"
        >
          <span className="text-3xl">
            🛡️
          </span>

          <span className="text-[10px] font-bold mt-0.5">
            FlowShield
          </span>
        </button>
      )}

      {/* Full FlowShield View */}
      {isOpen && (
        <div className="fixed inset-0 z-[100] bg-slate-50 overflow-y-auto">

          {/* FlowShield Header */}
          <header className="sticky top-0 z-50 bg-white border-b border-slate-200">

            <div className="max-w-md mx-auto px-4 py-4 flex items-center gap-3">

              <button
                onClick={() => setIsOpen(false)}
                className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center text-lg"
              >
                ←
              </button>

              <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white">
                🛡️
              </div>

              <div>
                <h1 className="font-bold text-slate-900">
                  FlowShield
                </h1>

                <p className="text-xs text-slate-500">
                  Financial Safety
                </p>
              </div>

            </div>

          </header>

          {/* Dashboard */}
          <div className="max-w-md mx-auto">

            <WorkerDashboard
              workerId={workerId}
            />

          </div>

        </div>
      )}
    </>
  );
}

export default FlowShieldWidget;