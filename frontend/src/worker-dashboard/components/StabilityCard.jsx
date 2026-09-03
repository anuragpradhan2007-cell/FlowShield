function StabilityCard({ score }) {
  let riskLevel;
  let message;

  if (score >= 70) {
    riskLevel = "Stable";
    message = "Your financial situation looks healthy.";
  } else if (score >= 40) {
    riskLevel = "At Risk";
    message = "Your income is less stable right now.";
  } else {
    riskLevel = "Critical";
    message = "Your finances may need attention.";
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Stability Score
          </h2>

          <p className="text-sm text-slate-500">
            Your financial safety level
          </p>
        </div>

        <span
          className={`px-3 py-1 rounded-full text-sm font-semibold ${
            score >= 70
              ? "bg-green-100 text-green-700"
              : score >= 40
              ? "bg-yellow-100 text-yellow-700"
              : "bg-red-100 text-red-700"
          }`}
        >
          {riskLevel}
        </span>
      </div>

      <div className="flex items-end gap-2">
        <p className="text-5xl font-bold text-slate-900">
          {score}
        </p>

        <p className="text-slate-400 mb-2">
          / 100
        </p>
      </div>

      <div className="mt-4 h-3 bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${
            score >= 70
              ? "bg-green-500"
              : score >= 40
              ? "bg-yellow-500"
              : "bg-red-500"
          }`}
          style={{ width: `${score}%` }}
        />
      </div>

      <p className="mt-3 text-sm text-slate-600">
        {message}
      </p>
    </div>
  );
}

export default StabilityCard;