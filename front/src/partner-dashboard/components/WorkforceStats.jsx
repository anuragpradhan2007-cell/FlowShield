function WorkforceStats({ workforce }) {
  const stablePercentage = Math.round(
    (workforce.stable / workforce.total) * 100
  );

  const atRiskPercentage = Math.round(
    (workforce.atRisk / workforce.total) * 100
  );

  const criticalPercentage = Math.round(
    (workforce.critical / workforce.total) * 100
  );

  return (
    <section>
      <h2>Workforce Financial Health</h2>

      <div>
        <h3>Stable</h3>
        <p>{workforce.stable}</p>
        <p>{stablePercentage}%</p>
      </div>

      <div>
        <h3>At Risk</h3>
        <p>{workforce.atRisk}</p>
        <p>{atRiskPercentage}%</p>
      </div>

      <div>
        <h3>Critical</h3>
        <p>{workforce.critical}</p>
        <p>{criticalPercentage}%</p>
      </div>

      <div>
        <h3>Total Workers</h3>
        <p>{workforce.total}</p>
      </div>
    </section>
  );
}

export default WorkforceStats;