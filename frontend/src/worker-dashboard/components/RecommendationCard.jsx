import { useState } from "react";

function RecommendationCard({ score }) {
  const [message, setMessage] = useState("");

  let title;
  let recommendation;
  let action;

  if (score >= 70) {
    title = "Build your emergency fund";
    recommendation =
      "Your income is stable. Keep saving a small amount from your earnings.";
    action = "Save ₹100";
  } else if (score >= 40) {
    title = "Strengthen your safety net";
    recommendation =
      "Your income is less stable right now. Try saving a little more this week.";
    action = "Save ₹100";
  } else {
    title = "Protect your finances";
    recommendation =
      "Your income has dropped significantly. Consider using your emergency fund if needed.";
    action = "View Support";
  }

  const handleAction = () => {
    if (score >= 40) {
      setMessage("₹100 savings added to your emergency fund.");
    } else {
      setMessage(
        "Support options are available. Please review your emergency fund and available assistance."
      );
    }
  };

  return (
    <div className="rounded-xl bg-blue-50 border border-blue-100 p-5">
      <div className="flex items-start gap-4">
        <div className="w-11 h-11 shrink-0 rounded-full bg-blue-600 text-white flex items-center justify-center text-xl">
          💡
        </div>

        <div className="flex-1">
          <p className="text-sm font-semibold text-blue-600">
            Recommendation
          </p>

          <h2 className="text-xl font-bold text-slate-900 mt-1">
            {title}
          </h2>

          <p className="text-sm text-slate-600 mt-2 leading-6">
            {recommendation}
          </p>

          <button
            onClick={handleAction}
            className="mt-4 px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition"
          >
            {action}
          </button>

          {message && (
            <div className="mt-3 p-3 bg-white border border-blue-100 rounded-lg">
              <p className="text-sm font-medium text-green-700">
                ✓ {message}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default RecommendationCard;