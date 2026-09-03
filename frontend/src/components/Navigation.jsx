function Navigation({ currentView, onChange }) {
  return (
    <nav className="w-full bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

        <div>
          <h1 className="text-xl font-bold text-slate-900">
            FlowShield
          </h1>

          <p className="text-sm text-slate-500">
            Financial Safety Platform
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => onChange("worker")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              currentView === "worker"
                ? "bg-blue-600 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Worker
          </button>

          <button
            onClick={() => onChange("widget")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              currentView === "widget"
                ? "bg-blue-600 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Widget
          </button>
        </div>

      </div>
    </nav>
  );
}

export default Navigation;