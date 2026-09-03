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
    <div>
      <h2>Recommendation</h2>

      <h3>{title}</h3>

      <p>{recommendation}</p>

      <button onClick={handleAction}>
        {action}
      </button>

      {message && <p>{message}</p>}
    </div>
  );
}

export default RecommendationCard;