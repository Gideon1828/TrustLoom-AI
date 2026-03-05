import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  RadialLinearScale,
  BarElement,
  ArcElement,
  LineElement,
  PointElement,
  Filler,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Doughnut, Radar, Line } from "react-chartjs-2";

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  RadialLinearScale,
  BarElement,
  ArcElement,
  LineElement,
  PointElement,
  Filler,
  Title,
  Tooltip,
  Legend,
);

export const ScoreBreakdownChart = ({ scoreBreakdown }) => {
  const bertScore = scoreBreakdown.resume_quality?.score || 0;
  const lstmScore = scoreBreakdown.project_realism?.score || 0;
  const heuristicScore = scoreBreakdown.profile_validation?.score || 0;

  const data = {
    labels: [
      "Resume Quality (BERT)",
      "Project Realism (LSTM)",
      "Profile Validation",
    ],
    datasets: [
      {
        label: "Score",
        data: [bertScore, lstmScore, heuristicScore],
        backgroundColor: [
          "rgba(59, 130, 246, 0.8)",
          "rgba(16, 185, 129, 0.8)",
          "rgba(245, 158, 11, 0.8)",
        ],
        borderColor: [
          "rgba(59, 130, 246, 1)",
          "rgba(16, 185, 129, 1)",
          "rgba(245, 158, 11, 1)",
        ],
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: "Score Breakdown by Component",
        font: {
          size: 16,
          weight: "bold",
        },
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            const label = context.dataset.label || "";
            const value = context.parsed.y || 0;
            const maxScores = {
              "Resume Quality (BERT)": 25,
              "Project Realism (LSTM)": 45,
              "Profile Validation": 30,
            };
            const max = maxScores[context.label] || 100;
            return `${label}: ${value}/${max}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 50,
        ticks: {
          font: {
            size: 12,
          },
        },
        grid: {
          color: "rgba(0, 0, 0, 0.05)",
        },
      },
      x: {
        ticks: {
          font: {
            size: 11,
          },
        },
        grid: {
          display: false,
        },
      },
    },
  };

  return (
    <div style={{ height: "300px", position: "relative" }}>
      <Bar data={data} options={options} />
    </div>
  );
};

export const TrustScoreDoughnut = ({ trustScore, maxScore = 100 }) => {
  const remaining = maxScore - trustScore;

  const getRiskColor = (score) => {
    if (score >= 80) return "rgba(16, 185, 129, 0.9)";
    if (score >= 55) return "rgba(245, 158, 11, 0.9)";
    return "rgba(239, 68, 68, 0.9)";
  };

  const data = {
    labels: ["Trust Score", "Remaining"],
    datasets: [
      {
        data: [trustScore, remaining],
        backgroundColor: [getRiskColor(trustScore), "rgba(229, 231, 235, 0.3)"],
        borderColor: [
          getRiskColor(trustScore).replace("0.9", "1"),
          "rgba(229, 231, 235, 0.5)",
        ],
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: "Overall Trust Score",
        font: {
          size: 16,
          weight: "bold",
        },
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            if (context.label === "Trust Score") {
              return `Trust Score: ${trustScore}/${maxScore}`;
            }
            return null;
          },
        },
      },
    },
    cutout: "75%",
  };

  return (
    <div style={{ height: "300px", position: "relative" }}>
      <Doughnut data={data} options={options} />
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          textAlign: "center",
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            fontSize: "32px",
            fontWeight: "bold",
            color: getRiskColor(trustScore).replace("0.9", "1"),
          }}
        >
          {trustScore}
        </div>
        <div style={{ fontSize: "14px", color: "#6b7280" }}>
          out of {maxScore}
        </div>
      </div>
    </div>
  );
};

export const ComponentMaxScoresChart = ({ scoreBreakdown }) => {
  const bertScore = scoreBreakdown.resume_quality?.score || 0;
  const lstmScore = scoreBreakdown.project_realism?.score || 0;
  const heuristicScore = scoreBreakdown.profile_validation?.score || 0;

  const data = {
    labels: ["BERT (25)", "LSTM (45)", "Heuristic (30)"],
    datasets: [
      {
        label: "Achieved",
        data: [bertScore, lstmScore, heuristicScore],
        backgroundColor: "rgba(59, 130, 246, 0.8)",
        borderColor: "rgba(59, 130, 246, 1)",
        borderWidth: 2,
      },
      {
        label: "Maximum",
        data: [25, 45, 30],
        backgroundColor: "rgba(229, 231, 235, 0.5)",
        borderColor: "rgba(229, 231, 235, 1)",
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: "top",
      },
      title: {
        display: true,
        text: "Score vs Maximum Possible",
        font: {
          size: 16,
          weight: "bold",
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 50,
        ticks: {
          stepSize: 10,
        },
        grid: {
          color: "rgba(0, 0, 0, 0.05)",
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
  };

  return (
    <div style={{ height: "300px", position: "relative" }}>
      <Bar data={data} options={options} />
    </div>
  );
};
export const TrustRadarChart = ({ scoreBreakdown, explanations }) => {
  const isDark =
    document.documentElement.getAttribute("data-theme") === "dark";

  const pct = (val, max) =>
    max > 0 ? Math.round(((val ?? 0) / max) * 100) : 0;

  const bertRaw = scoreBreakdown?.resume_quality?.score ?? 0;
  const lstmRaw = scoreBreakdown?.project_realism?.score ?? 0;
  const ghRaw = explanations?.github?.score ?? 0;
  const liRaw = explanations?.linkedin?.score ?? 0;
  const portRaw = explanations?.portfolio?.score ?? 0;
  const expRaw = explanations?.experience?.score ?? 0;

  const values = [
    pct(bertRaw, 25),
    pct(lstmRaw, 45),
    pct(ghRaw, 10),
    pct(liRaw, 10),
    pct(portRaw, 5),
    pct(expRaw, 5),
  ];

  const rawMaxPairs = [
    [bertRaw, 25],
    [lstmRaw, 45],
    [ghRaw, 10],
    [liRaw, 10],
    [portRaw, 5],
    [expRaw, 5],
  ];

  const gridColor = isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)";
  const tickColor = isDark ? "#a78bfa" : "#7c3aed";
  const labelColor = isDark ? "#cbd5e1" : "#374151";

  const data = {
    labels: [
      "Language Quality",
      "Project Realism",
      "GitHub Activity",
      "LinkedIn Profile",
      "Portfolio",
      "Experience Match",
    ],
    datasets: [
      {
        label: "Profile Strength",
        data: values,
        backgroundColor: "rgba(139,92,246,0.18)",
        borderColor: "rgba(139,92,246,0.9)",
        borderWidth: 2,
        pointBackgroundColor: "rgba(139,92,246,0.9)",
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const idx = ctx.dataIndex;
            const [raw, max] = rawMaxPairs[idx];
            return ` ${raw} / ${max} pts → ${ctx.parsed.r}%`;
          },
        },
      },
    },
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 25,
          color: tickColor,
          backdropColor: "transparent",
          callback: (v) => `${v}%`,
          font: { size: 10 },
        },
        grid: { color: gridColor },
        angleLines: { color: gridColor },
        pointLabels: {
          color: labelColor,
          font: { size: 11, weight: "600" },
        },
      },
    },
  };

  return (
    <div style={{ height: "340px", position: "relative" }}>
      <Radar data={data} options={options} />
    </div>
  );
};

/**
 * ProfileStrengthLineChart — Area/line chart showing the same 6 profile
 * dimensions as the radar but in a sleek line-chart format.
 */
export const ProfileStrengthLineChart = ({ scoreBreakdown, explanations }) => {
  const isDark =
    document.documentElement.getAttribute("data-theme") === "dark";

  const pct = (val, max) =>
    max > 0 ? Math.round(((val ?? 0) / max) * 100) : 0;

  const bertRaw = scoreBreakdown?.resume_quality?.score ?? 0;
  const lstmRaw = scoreBreakdown?.project_realism?.score ?? 0;
  const ghRaw = explanations?.github?.score ?? 0;
  const liRaw = explanations?.linkedin?.score ?? 0;
  const portRaw = explanations?.portfolio?.score ?? 0;
  const expRaw = explanations?.experience?.score ?? 0;

  const labels = [
    "Language Quality",
    "Project Realism",
    "GitHub Activity",
    "LinkedIn Profile",
    "Portfolio",
    "Experience Match",
  ];

  const values = [
    pct(bertRaw, 25),
    pct(lstmRaw, 45),
    pct(ghRaw, 10),
    pct(liRaw, 10),
    pct(portRaw, 5),
    pct(expRaw, 5),
  ];

  const rawMaxPairs = [
    [bertRaw, 25],
    [lstmRaw, 45],
    [ghRaw, 10],
    [liRaw, 10],
    [portRaw, 5],
    [expRaw, 5],
  ];

  const gridColor = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)";
  const labelColor = isDark ? "#cbd5e1" : "#6b7280";

  const data = {
    labels,
    datasets: [
      {
        label: "Score %",
        data: values,
        fill: true,
        backgroundColor: isDark
          ? "rgba(56, 189, 248, 0.12)"
          : "rgba(56, 189, 248, 0.15)",
        borderColor: "#38bdf8",
        borderWidth: 2.5,
        pointBackgroundColor: "#38bdf8",
        pointBorderColor: isDark ? "#1e293b" : "#ffffff",
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        tension: 0.35,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: isDark ? "#1e293b" : "#ffffff",
        titleColor: isDark ? "#f1f5f9" : "#111827",
        bodyColor: isDark ? "#cbd5e1" : "#374151",
        borderColor: isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)",
        borderWidth: 1,
        cornerRadius: 8,
        padding: 10,
        boxPadding: 4,
        callbacks: {
          label: (ctx) => {
            const idx = ctx.dataIndex;
            const [raw, max] = rawMaxPairs[idx];
            return ` ${raw} / ${max} pts → ${ctx.parsed.y}%`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: labelColor,
          font: { size: 11, weight: "600" },
          maxRotation: 35,
          minRotation: 0,
        },
        border: { display: false },
      },
      y: {
        min: 0,
        max: 100,
        grid: { color: gridColor, drawBorder: false },
        border: { display: false },
        ticks: {
          color: labelColor,
          font: { size: 10 },
          stepSize: 25,
          callback: (v) => `${v}%`,
          padding: 8,
        },
      },
    },
  };

  return (
    <div style={{ height: "300px", position: "relative" }}>
      <Line data={data} options={options} />
    </div>
  );
};