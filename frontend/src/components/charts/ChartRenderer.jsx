import React from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";

const PALETTE = ["#00F2FE", "#9B51E0", "#10b981", "#f59e0b", "#ec4899", "#38bdf8", "#8b5cf6"];

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
        <div className="bg-[#121829]/95 border border-white/10 p-2.5 rounded-xl shadow-2xl text-xs backdrop-blur-md">
          <p className="font-bold text-white mb-1">{label || payload[0]?.payload[x_axis] || payload[0]?.name}</p>
          {payload.map((item, idx) => (
            <p key={idx} className="text-[#00F2FE] font-semibold">
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
            <CartesianGrid strokeDasharray="3 3" stroke="#121829" />
            <XAxis dataKey={x_axis || "date"} stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey={y_axis || "value"} stroke="#00F2FE" strokeWidth={2.5} dot={{ r: 2, fill: "#00F2FE" }} activeDot={{ r: 5 }} />
          </LineChart>
        ) : chart_type === "bar" ? (
          <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#121829" />
            <XAxis dataKey={x_axis || "category"} stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={y_axis || "value"} fill="#00F2FE" radius={[4, 4, 0, 0]}>
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
            <CartesianGrid strokeDasharray="3 3" stroke="#121829" />
            <XAxis dataKey={x_axis || "x"} stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis dataKey={y_axis || "y"} stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Scatter name="Points" data={data} fill="#9B51E0" />
          </ScatterChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
