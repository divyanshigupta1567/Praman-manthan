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
    <section className="trend-panel" aria-label="Complaint trend" data-reveal data-reveal-delay="3">
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
            <CartesianGrid stroke="#D3DAE4" strokeDasharray="3 3" />
            <XAxis dataKey="date" stroke="#6F7C8E" fontSize={12} tickLine={false} />
            <YAxis stroke="#6F7C8E" fontSize={12} tickLine={false} allowDecimals={false} />
            <Tooltip
              contentStyle={{ background: "#EEF2F7", border: "1px solid rgba(151,166,189,0.3)", borderRadius: 12, boxShadow: "6px 6px 16px rgba(157,172,194,0.45)", color: "#27313F" }}
              labelStyle={{ color: "#6F7C8E" }}
            />
            <Legend wrapperStyle={{ fontSize: 12, color: "#6F7C8E" }} />
            <Line
              type="monotone"
              dataKey="complaint_count"
              name="Reports"
              stroke="#2C8391"
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
              stroke="#6F7C8E"
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
