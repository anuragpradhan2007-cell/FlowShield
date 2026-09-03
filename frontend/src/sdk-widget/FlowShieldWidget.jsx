import WorkerDashboard from "../worker-dashboard/WorkerDashboard";

function FlowShieldWidget({ workerId }) {
  return (
    <main className="min-h-screen bg-slate-200 py-4 sm:py-8">
      <div className="w-full max-w-md mx-auto bg-white sm:rounded-3xl sm:shadow-xl overflow-hidden">

        {/* Widget Header */}
        <header className="bg-blue-600 px-5 py-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-lg font-bold">
                FlowShield
              </p>

              <p className="text-xs text-blue-100">
                Your financial safety companion
              </p>
            </div>

            <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
              🛡️
            </div>
          </div>
        </header>

        {/* Worker Dashboard */}
        <div>
          <WorkerDashboard workerId={workerId} />
        </div>

      </div>
    </main>
  );
}

export default FlowShieldWidget;