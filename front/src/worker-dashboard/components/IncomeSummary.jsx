function IncomeSummary({ weeklyIncome, incomeChange }) {
  return (
    <div>
      <h2>This Week</h2>
      <p>₹{weeklyIncome}</p>
      <p>{incomeChange}% from last week</p>
    </div>
  );
}

export default IncomeSummary;