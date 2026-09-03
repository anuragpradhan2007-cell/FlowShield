function IncomeSummary({ weeklyIncome, incomeChange }) {
  const isPositive = incomeChange >= 0;

  return (
    <div>
      <h2 className="text-lg font-semibold text-slate-900">
        This Week
      </h2>

      <p className="text-sm text-slate-500 mt-1">
        Your total earnings this week
      </p>

      <div className="mt-5 flex items-end gap-3">
        <p className="text-4xl font-bold text-slate-900">
          ₹{weeklyIncome.toLocaleString("en-IN")}
        </p>

        <span
          className={`mb-1 px-2.5 py-1 rounded-full text-sm font-semibold ${
            isPositive
              ? "bg-green-100 text-green-700"
              : "bg-red-100 text-red-700"
          }`}
        >
          {isPositive ? "+" : ""}
          {incomeChange}%
        </span>
      </div>

      <p className="text-sm text-slate-500 mt-2">
        compared with last week
      </p>
    </div>
  );
}

export default IncomeSummary;