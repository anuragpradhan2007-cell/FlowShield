import WorkerDashboard from "../worker-dashboard/WorkerDashboard";

function FlowShieldWidget({ workerId, token }) {
  return (
    <div>
      <WorkerDashboard workerId={workerId} token={token} />
    </div>
  );
}

export default FlowShieldWidget;