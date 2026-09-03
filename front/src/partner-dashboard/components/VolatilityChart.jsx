import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";

function VolatilityChart({ data }) {
  return (
    <section>
      <h2>Income Volatility</h2>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="month" />

          <YAxis />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="volatility"
            stroke="#2563eb"
          />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}

export default VolatilityChart;