function StabilityCard({ score }) {
  let riskLevel;

  if (score >= 70) {
    riskLevel = "Stable";
  } else if (score >= 40) {
    riskLevel = "At Risk";
  } else {
    riskLevel = "Critical";
  }

  return (
    <div>
      <h2>Stability Score</h2>

      <p>{score} / 100</p>

      <p>{riskLevel}</p>
    </div>
  );
}

export default StabilityCard;