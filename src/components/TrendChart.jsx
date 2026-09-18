import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";
import SectionState from "./SectionState";

// trends: array of Trend Data Points (Section 7). Plots complaint_count
// against baseline per day so a spike reads as a visual gap between the
// two lines, not a number someone has to compute in their head.
export default function TrendChart({ trends, loading, error, onRetry }) {
  const isEmpty = !loading && !error && (!trends || trends.length === 0);

  return (
    <section className="trend-panel" aria-label="Complaint trend">
      <h2 className="panel-title">Trend vs. Baseline</h2>
      <SectionState
        loading={loading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="Not enough history to chart a trend yet."
        onRetry={onRetry}
        skeletonHeight={260}
      >
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={trends} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#1E262F" strokeDasharray="3 3" />
            <XAxis dataKey="date" stroke="#8A97A3" fontSize={12} tickLine={false} />
            <YAxis stroke="#8A97A3" fontSize={12} tickLine={false} allowDecimals={false} />
            <Tooltip
              contentStyle={{ background: "#12181F", border: "1px solid #1E262F", color: "#E6EBF0" }}
              labelStyle={{ color: "#8A97A3" }}
            />
            <Legend wrapperStyle={{ fontSize: 12, color: "#8A97A3" }} />
            <Line
              type="monotone"
              dataKey="complaint_count"
              name="Reports"
              stroke="#4FB8C9"
              strokeWidth={2}
              dot={false}
              isAnimationActive
              animationDuration={700}
              animationEasing="ease-out"
            />
            <Line
              type="monotone"
              dataKey="baseline"
              name="Baseline"
              stroke="#8A97A3"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              dot={false}
              isAnimationActive
              animationDuration={700}
              animationEasing="ease-out"
            />
          </LineChart>
        </ResponsiveContainer>
      </SectionState>
    </section>
  );
}
