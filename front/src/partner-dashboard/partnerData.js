const partnerData = {
  partnerId: 1,
  partnerName: "FlowShield Partner",

  workforce: {
    total: 1000,
    stable: 720,
    atRisk: 210,
    critical: 70
  },

  incomeVolatility: [
    { month: "Jan", volatility: 12 },
    { month: "Feb", volatility: 15 },
    { month: "Mar", volatility: 11 },
    { month: "Apr", volatility: 19 },
    { month: "May", volatility: 16 },
    { month: "Jun", volatility: 22 }
  ],

  atRiskWorkers: [
    {
      id: 101,
      name: "Rahul",
      score: 48,
      incomeChange: -18,
      risk: "At Risk"
    },
    {
      id: 102,
      name: "Arjun",
      score: 35,
      incomeChange: -31,
      risk: "Critical"
    },
    {
      id: 103,
      name: "Sameer",
      score: 52,
      incomeChange: -12,
      risk: "At Risk"
    },
    {
      id: 104,
      name: "Vikram",
      score: 38,
      incomeChange: -25,
      risk: "Critical"
    }
  ]
};

export default partnerData;