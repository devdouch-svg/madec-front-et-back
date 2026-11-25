import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";
import type { LucideIcon } from "lucide-react";

/* Minia dashboard building blocks (my-madec-frontend-test-v2-UI/Admin,
   views/index.ejs + assets/js/pages/dashboard.init.js), rendered with
   react-apexcharts instead of jQuery init scripts. */

import { MINIA_PRIMARY, MINIA_SUCCESS, MINIA_SOFT, MINIA_MUTED, STATUS_CHART_COLORS, dayLabels } from "./chartData";

const CHART_ANIMATION: ApexOptions["chart"] = {
  animations: {
    enabled: true,
    speed: 900,
    animateGradually: { enabled: true, delay: 90 },
    dynamicAnimation: { enabled: true, speed: 400 },
  },
};

/* ── Animated counter for KPI digits ─────────────────────────────────────── */

function easeOutCubic(t: number) {
  return 1 - Math.pow(1 - t, 3);
}

function useCountUp(target: number, durationMs = 900, decimals = 0) {
  const [value, setValue] = useState(0);
  const prefersReduced =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    if (prefersReduced || !Number.isFinite(target)) {
      setValue(target);
      return;
    }
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      setValue(target * easeOutCubic(t));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, durationMs, prefersReduced]);

  if (decimals > 0) return Number(value.toFixed(decimals));
  return Math.round(value);
}

function AnimatedStatValue({
  value,
  rawValue,
  formatValue,
}: {
  value: string | number;
  rawValue?: number;
  formatValue?: (n: number) => string;
}) {
  const numeric = rawValue ?? (typeof value === "number" ? value : undefined);
  const target = numeric ?? 0;
  const decimals = numeric != null && !Number.isInteger(numeric) ? 2 : 0;
  const animated = useCountUp(target, 950, decimals);

  if (numeric == null) {
    return <span className="stat-value-animate">{value}</span>;
  }

  const display = formatValue
    ? formatValue(animated)
    : animated.toLocaleString("fr-MA");

  return <span className="stat-value-animate">{display}</span>;
}

/* ── mini-chart1..4 : line sparkline, height 50, smooth, width 2 ─────────── */

export function MiniSparkline({ data, color = MINIA_PRIMARY }: { data: number[]; color?: string }) {
  const options: ApexOptions = {
    chart: {
      type: "line",
      sparkline: { enabled: true },
      ...CHART_ANIMATION,
    },
    colors: [color],
    stroke: { curve: "smooth", width: 2.5 },
    markers: {
      size: 0,
      hover: { size: 4 },
    },
    tooltip: {
      fixed: { enabled: false },
      x: { show: false },
      y: { title: { formatter: () => "" } },
      marker: { show: false },
    },
  };
  return <Chart type="line" height={56} series={[{ data }]} options={options} />;
}

/* ── Widget card ("My Wallet" card of the Minia dashboard) ───────────────── */

export type BadgeTone = "success" | "danger" | "warning" | "primary" | "neutral";

const BADGE_TONES: Record<BadgeTone, string> = {
  success: "bg-madec-successTint text-[#1d7f57]",
  danger: "bg-madec-dangerTint text-[#d0413e]",
  warning: "bg-madec-warningTint text-[#997332]",
  primary: "bg-madec-tint text-madec-primary",
  neutral: "bg-madec-surface text-madec-secondary",
};

const ICON_TONES: Record<BadgeTone, string> = {
  success: "bg-madec-successTint text-madec-success",
  danger: "bg-madec-dangerTint text-madec-danger",
  warning: "bg-madec-warningTint text-[#c9891a]",
  primary: "bg-madec-tint text-madec-primary",
  neutral: "bg-madec-surface text-madec-secondary",
};

export function StatWidgetCard({
  label,
  value,
  rawValue,
  formatValue,
  spark,
  badge,
  badgeTone = "primary",
  caption,
  href,
  icon: Icon,
  iconTone,
}: {
  label: string;
  value: string | number;
  /** Numeric source for count-up animation (e.g. amount before formatMAD). */
  rawValue?: number;
  formatValue?: (n: number) => string;
  /** sparkline series; omitted → value takes the full width */
  spark?: number[];
  badge?: ReactNode;
  badgeTone?: BadgeTone;
  caption?: string;
  href?: string;
  icon?: LucideIcon;
  iconTone?: BadgeTone;
}) {
  const tone = iconTone ?? badgeTone;
  const inner = (
    <div className="card card--stat h-full !p-5 transition-transform duration-300 hover:-translate-y-0.5">
      <div className="mb-3 flex items-start justify-between gap-2">
        <span className="block truncate text-sm leading-none text-madec-muted">{label}</span>
        {Icon && (
          <span
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-lg ${ICON_TONES[tone]}`}
          >
            <Icon size={20} strokeWidth={1.75} />
          </span>
        )}
      </div>
      <div className="flex items-end justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h4 className="mb-3 truncate text-[28px] font-semibold leading-tight tracking-tight text-madec-text">
            <AnimatedStatValue
              value={value}
              rawValue={rawValue}
              formatValue={formatValue}
            />
          </h4>
        </div>
        {spark && spark.length > 1 && (
          <div className="mb-2 w-[42%] shrink-0 opacity-90">
            <MiniSparkline data={spark} />
          </div>
        )}
      </div>
      <div className="whitespace-nowrap text-[13px]">
        {badge != null && (
          <span className={`badge ${BADGE_TONES[badgeTone]}`}>{badge}</span>
        )}
        {caption && <span className="ml-1.5 text-madec-muted">{caption}</span>}
      </div>
    </div>
  );
  if (href) return <Link to={href} className="block h-full">{inner}</Link>;
  return inner;
}

/* ── Pie card ("Wallet Balance" card: pie + legend rows) ─────────────────── */

export function StatusPie({
  entries,
  height = 180,
}: {
  entries: [status: string, count: number, label: string][];
  height?: number;
}) {
  const options: ApexOptions = {
    chart: {
      type: "donut",
      ...CHART_ANIMATION,
    },
    colors: entries.map(([s]) => STATUS_CHART_COLORS[s] ?? "#a8aada"),
    labels: entries.map(([, , label]) => label),
    stroke: { width: 0 },
    legend: { show: false },
    dataLabels: { enabled: false },
    plotOptions: {
      pie: {
        donut: {
          size: "72%",
          labels: {
            show: true,
            name: { show: true, fontSize: "12px", color: "#74788d", offsetY: 14 },
            value: {
              show: true,
              fontSize: "22px",
              fontWeight: 600,
              color: "#313533",
              offsetY: -8,
            },
            total: {
              show: true,
              label: "Total",
              fontSize: "12px",
              color: "#74788d",
              formatter: (w) =>
                String(w.globals.seriesTotals.reduce((a: number, b: number) => a + b, 0)),
            },
          },
        },
      },
    },
  };
  return (
    <Chart
      type="donut"
      height={height}
      series={entries.map(([, n]) => n)}
      options={options}
    />
  );
}

/* ── Radial gauge ("Invested Overview" card) ─────────────────────────────── */

export function RadialGauge({
  percent,
  label,
  color = MINIA_PRIMARY,
}: {
  percent: number;
  label: string;
  color?: string;
}) {
  const options: ApexOptions = {
    chart: {
      type: "radialBar",
      ...CHART_ANIMATION,
    },
    colors: [color],
    plotOptions: {
      radialBar: {
        startAngle: -115,
        endAngle: 115,
        hollow: { size: "70%" },
        track: { background: "#e9e9ef", strokeWidth: "100%" },
        dataLabels: {
          name: {
            show: true,
            fontSize: "13px",
            color: "#74788d",
            offsetY: 60,
          },
          value: {
            show: true,
            fontSize: "24px",
            fontWeight: 600,
            color: "#313533",
            offsetY: -10,
            formatter: (v) => `${Math.round(v)}%`,
          },
        },
      },
    },
    fill: {
      type: "gradient",
      gradient: {
        shade: "dark",
        type: "horizontal",
        gradientToColors: ["#777aca"],
        shadeIntensity: 0.15,
        inverseColors: false,
        opacityFrom: 1,
        opacityTo: 1,
        stops: [0, 50, 65, 91],
      },
    },
    stroke: { dashArray: 4 },
    labels: [label],
  };
  return <Chart type="radialBar" height={240} series={[Math.min(100, percent)]} options={options} />;
}

/* ── Market Overview (Minia stacked columns) ─────────────────────────────── */

export function MarketOverviewChart({
  counts,
  amounts,
  categories: categoriesProp,
  height = 320,
}: {
  counts: number[];
  amounts: number[];
  categories?: string[];
  height?: number;
}) {
  const categories = categoriesProp ?? dayLabels(counts.length);
  // Scale amounts to same visual range as counts for stacked dual-series feel
  const maxAmt = Math.max(...amounts, 1);
  const maxCnt = Math.max(...counts, 1);
  const scaledAmt = amounts.map((a) => Number(((a / maxAmt) * maxCnt).toFixed(2)));

  const options: ApexOptions = {
    chart: {
      type: "bar",
      stacked: true,
      toolbar: { show: false },
      ...CHART_ANIMATION,
    },
    plotOptions: {
      bar: { columnWidth: "28%", borderRadius: 3 },
    },
    colors: [MINIA_PRIMARY, MINIA_SUCCESS],
    fill: { opacity: 1 },
    dataLabels: { enabled: false },
    legend: {
      show: true,
      position: "top",
      horizontalAlign: "right",
      fontSize: "12px",
      markers: { size: 6 },
    },
    grid: {
      borderColor: "#e9e9ef",
      strokeDashArray: 3,
      padding: { top: 0, right: 8, bottom: 0, left: 8 },
    },
    yaxis: {
      labels: {
        style: { colors: "#74788d", fontSize: "11px" },
        formatter: (y) => String(Math.round(y)),
      },
    },
    xaxis: {
      categories,
      labels: {
        rotate: -45,
        style: { colors: "#74788d", fontSize: "10px" },
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    tooltip: {
      shared: true,
      intersect: false,
      y: {
        formatter: (val, opts) => {
          if (opts?.seriesIndex === 1) {
            const real = amounts[opts.dataPointIndex] ?? 0;
            return `${real.toLocaleString("fr-MA", { maximumFractionDigits: 0 })} MAD`;
          }
          return `${Math.round(val)} commande${Math.round(val) > 1 ? "s" : ""}`;
        },
      },
    },
  };

  return (
    <Chart
      type="bar"
      height={height}
      series={[
        { name: "Commandes", data: counts },
        { name: "CA (relatif)", data: scaledAmt },
      ]}
      options={options}
    />
  );
}

/* ── Activity area (orders + revenue trend) ──────────────────────────────── */

export function ActivityAreaChart({
  counts,
  amounts,
  categories: categoriesProp,
  height = 300,
}: {
  counts: number[];
  amounts: number[];
  categories?: string[];
  height?: number;
}) {
  const categories = categoriesProp ?? dayLabels(counts.length);
  const options: ApexOptions = {
    chart: {
      type: "area",
      toolbar: { show: false },
      zoom: { enabled: false },
      ...CHART_ANIMATION,
    },
    colors: [MINIA_PRIMARY, MINIA_SOFT],
    dataLabels: { enabled: false },
    stroke: { curve: "smooth", width: 2.5 },
    fill: {
      type: "gradient",
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.35,
        opacityTo: 0.05,
        stops: [0, 90, 100],
      },
    },
    legend: {
      show: true,
      position: "top",
      horizontalAlign: "right",
      fontSize: "12px",
    },
    grid: {
      borderColor: "#e9e9ef",
      strokeDashArray: 3,
    },
    xaxis: {
      categories,
      labels: {
        rotate: -45,
        style: { colors: "#74788d", fontSize: "10px" },
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: [
      {
        title: { text: "Commandes", style: { color: "#74788d", fontSize: "11px" } },
        labels: {
          style: { colors: "#74788d", fontSize: "11px" },
          formatter: (v) => String(Math.round(v)),
        },
      },
      {
        opposite: true,
        title: { text: "CA (MAD)", style: { color: "#74788d", fontSize: "11px" } },
        labels: {
          style: { colors: "#74788d", fontSize: "11px" },
          formatter: (v) =>
            v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(Math.round(v)),
        },
      },
    ],
    tooltip: {
      shared: true,
      y: {
        formatter: (val, opts) =>
          opts?.seriesIndex === 1
            ? `${Number(val).toLocaleString("fr-MA", { maximumFractionDigits: 0 })} MAD`
            : `${Math.round(val)}`,
      },
    },
  };

  return (
    <Chart
      type="area"
      height={height}
      series={[
        { name: "Commandes", type: "area", data: counts },
        { name: "Chiffre d'affaires", type: "area", data: amounts },
      ]}
      options={options}
    />
  );
}

/* ── Status columns (bar) ────────────────────────────────────────────────── */

export function StatusColumnsChart({
  entries,
  height = 280,
}: {
  entries: [status: string, count: number, label: string][];
  height?: number;
}) {
  const options: ApexOptions = {
    chart: {
      type: "bar",
      toolbar: { show: false },
      ...CHART_ANIMATION,
    },
    plotOptions: {
      bar: {
        distributed: true,
        borderRadius: 4,
        columnWidth: "45%",
      },
    },
    colors: entries.map(([s]) => STATUS_CHART_COLORS[s] ?? MINIA_MUTED),
    dataLabels: {
      enabled: true,
      style: { fontSize: "11px", fontWeight: 600, colors: ["#313533"] },
      offsetY: -4,
    },
    legend: { show: false },
    grid: {
      borderColor: "#e9e9ef",
      strokeDashArray: 3,
      padding: { top: 10 },
    },
    xaxis: {
      categories: entries.map(([, , label]) => label),
      labels: { style: { colors: "#74788d", fontSize: "11px" } },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: {
      labels: {
        style: { colors: "#74788d", fontSize: "11px" },
        formatter: (v) => String(Math.round(v)),
      },
    },
    tooltip: {
      y: { formatter: (v) => `${Math.round(v)} commande${Math.round(v) > 1 ? "s" : ""}` },
    },
  };

  return (
    <Chart
      type="bar"
      height={height}
      series={[{ name: "Commandes", data: entries.map(([, n]) => n) }]}
      options={options}
    />
  );
}

/* ── Status progress rows (Minia "Sales by Locations" style) ─────────────── */

export function StatusProgressList({
  entries,
}: {
  entries: [status: string, count: number, label: string][];
}) {
  const total = entries.reduce((s, [, n]) => s + n, 0) || 1;
  return (
    <ul className="space-y-4">
      {entries.map(([status, count, label]) => {
        const pct = Math.round((count / total) * 100);
        const color = STATUS_CHART_COLORS[status] ?? MINIA_PRIMARY;
        return (
          <li key={status}>
            <div className="mb-1.5 flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-madec-text">{label}</span>
              <span className="text-xs font-semibold text-madec-secondary">
                {count} · {pct}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-[#e9e9ef]">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{ width: `${pct}%`, backgroundColor: color }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

