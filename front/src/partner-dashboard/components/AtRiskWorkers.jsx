function AtRiskWorkers({ workers }) {
  return (
    <section>
      <h2>At-Risk Workers</h2>

      {workers.map((worker) => (
        <div key={worker.id}>
          <h3>{worker.name}</h3>

          <p>Stability Score: {worker.score}</p>

          <p>Income Change: {worker.incomeChange}%</p>

          <p>Risk: {worker.risk}</p>
        </div>
      ))}
    </section>
  );
}

export default AtRiskWorkers;