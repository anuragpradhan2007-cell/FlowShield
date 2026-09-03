import partnerData from "./partnerData";

import WorkforceStats from "./components/WorkforceStats";
import VolatilityChart from "./components/VolatilityChart";
import AtRiskWorkers from "./components/AtRiskWorkers";

function PartnerDashboard() {
  return (
    <main>
      <h1>{partnerData.partnerName}</h1>

      <WorkforceStats
        workforce={partnerData.workforce}
      />

      <VolatilityChart
        data={partnerData.incomeVolatility}
      />

      <AtRiskWorkers
        workers={partnerData.atRiskWorkers}
      />
    </main>
  );
}

export default PartnerDashboard;