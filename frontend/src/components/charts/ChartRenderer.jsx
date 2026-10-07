import React from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";

const PALETTE = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#3b82f6", "#8b5cf6", "#14b8a6"];

export default function ChartRenderer({ spec }) {
  if (!spec || !spec.data || spec.data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
        No chart data available for visualization.
      </div>
    );
  }

  const { chart_type, data, x_axis, y_axis, name_key, value_key } = spec;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-slate-700 p-2.5 rounded-lg shadow-xl text-xs">
          <p className="font-semibold text-slate-200 mb-1">{label || payload[0]?.payload[x_axis] || payload[0]?.name}</p>
          {payload.map((item, idx) => (
            <p key={idx} className="text-indigo-400 font-medium">
              {item.name || "Value"}: {typeof item.value === "number" ? item.value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : item.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        {chart_type === "line" ? (
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey={x_axis || "date"} stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey={y_axis || "value"} stroke="#6366f1" strokeWidth={2.5} dot={{ r: 2, fill: "#6366f1" }} activeDot={{ r: 5 }} />
          </LineChart>
        ) : chart_type === "bar" ? (
          <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey={x_axis || "category"} stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={y_axis || "value"} fill="#6366f1" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} />
              ))}
            </Bar>
          </BarChart>
        ) : chart_type === "donut" || chart_type === "pie" ? (
          <PieChart>
            <Pie
              data={data}
              dataKey={value_key || "value"}
              nameKey={name_key || "label"}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={4}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
          </PieChart>
        ) : (
          <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey={x_axis || "x"} stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis dataKey={y_axis || "y"} stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Scatter name="Points" data={data} fill="#8b5cf6" />
          </ScatterChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
