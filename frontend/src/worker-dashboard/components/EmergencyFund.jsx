import { useState } from "react";

function EmergencyFund({ current, target }) {
  const [fund, setFund] = useState(current);

  const percentage = Math.min(
    Math.round((fund / target) * 100),
    100
  );

  const handleSave = () => {
    if (fund + 100 <= target) {
      setFund(fund + 100);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Emergency Fund
          </h2>

          <p className="text-sm text-slate-500 mt-1">
            Money saved for unexpected needs
          </p>
        </div>

        <span className="text-sm font-semibold text-blue-600">
          {percentage}%
        </span>
      </div>

      <div className="mt-5 flex items-end gap-2">
        <p className="text-3xl font-bold text-slate-900">
          ₹{fund.toLocaleString("en-IN")}
        </p>

        <p className="text-sm text-slate-500 mb-1">
          / ₹{target.toLocaleString("en-IN")}
        </p>
      </div>

      <div className="mt-4 h-3 bg-slate-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-600 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="mt-5 flex items-center justify-between gap-4">
        <p className="text-sm text-slate-500">
          ₹{Math.max(target - fund, 0).toLocaleString("en-IN")} left to reach your goal
        </p>

        {fund < target ? (
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition"
          >
            Save ₹100
          </button>
        ) : (
          <span className="text-sm font-semibold text-green-600">
            Goal reached 🎉
          </span>
        )}
      </div>
    </div>
  );
}

export default EmergencyFund;