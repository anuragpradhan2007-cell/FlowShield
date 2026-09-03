import { useState } from "react";

function EmergencyFund({ current, target }) {
  const [fund, setFund] = useState(current);

  const percentage = Math.round((fund / target) * 100);

  const handleSave = () => {
    if (fund + 100 <= target) {
      setFund(fund + 100);
    }
  };

  return (
    <div>
      <h2>Emergency Fund</h2>

      <p>
        ₹{fund} / ₹{target}
      </p>

      <p>{percentage}% saved</p>

      {fund < target ? (
        <button onClick={handleSave}>
          Save ₹100
        </button>
      ) : (
        <p>Emergency fund goal reached! 🎉</p>
      )}
    </div>
  );
}

export default EmergencyFund;