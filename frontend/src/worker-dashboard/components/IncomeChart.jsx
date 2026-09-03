import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";

function IncomeChart({ data }) {
  return (
    <div>
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Income Trend
        </h2>

        <p className="text-sm text-slate-500 mt-1">
          Your earnings over the last 7 days
        </p>
      </div>

      <div className="w-full h-[250px] sm:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{
              top: 10,
              right: 10,
              left: -15,
              bottom: 5
            }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              vertical={false}
            />

            <XAxis
              dataKey="day"
              tick={{
                fill: "#64748b",
                fontSize: 12
              }}
              axisLine={false}
              tickLine={false}
            />

            <YAxis
              tick={{
                fill: "#64748b",
                fontSize: 12
              }}
              axisLine={false}
              tickLine={false}
              width={45}
            />

            <Tooltip
              formatter={(value) => [
                `₹${Number(value).toLocaleString("en-IN")}`,
                "Income"
              ]}
              contentStyle={{
                borderRadius: "10px",
                border: "1px solid #e2e8f0",
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)"
              }}
            />

            <Line
              type="monotone"
              dataKey="income"
              stroke="#2563eb"
              strokeWidth={3}
              dot={{
                r: 4,
                fill: "#2563eb"
              }}
              activeDot={{
                r: 6
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default IncomeChart;