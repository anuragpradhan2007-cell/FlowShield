const workerData = {
  id: 1,
  name: "Rahul",
  role: "Delivery Partner",

  stabilityScore: 78,
  riskLevel: "Stable",

  weeklyIncome: 4850,
  incomeChange: 12,

  emergencyFund: 3200,
  emergencyTarget: 5000,

  incomeHistory: [
    { day: "Mon", income: 620 },
    { day: "Tue", income: 750 },
    { day: "Wed", income: 580 },
    { day: "Thu", income: 820 },
    { day: "Fri", income: 690 },
    { day: "Sat", income: 910 },
    { day: "Sun", income: 480 }
  ],

  recommendation: {
    title: "Build your emergency fund",
    message: "Save ₹100 today to make your emergency fund stronger.",
    action: "Save ₹100"
  }
};

export default workerData;