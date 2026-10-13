"use client";

import type { Level } from "@/lib/api";
import { useLang } from "@/lib/i18n";

export const LEVEL_COLOR: Record<Level, string> = {
  LOW: "#15803d",
  MEDIUM: "#b45309",
  HIGH: "#b91c1c",
};

const BANDS: { from: number; to: number; color: string }[] = [
  { from: 0, to: 30, color: "#cfe8d6" },
  { from: 30, to: 60, color: "#f6dfb9" },
  { from: 60, to: 100, color: "#f3c4c0" },
];

function polar(cx: number, cy: number, r: number, value: number) {
  const angle = Math.PI * (1 - value / 100);
  return { x: cx + r * Math.cos(angle), y: cy - r * Math.sin(angle) };
}

function arc(cx: number, cy: number, r: number, from: number, to: number) {
  const a = polar(cx, cy, r, from);
  const b = polar(cx, cy, r, to);
  return `M ${a.x} ${a.y} A ${r} ${r} 0 0 1 ${b.x} ${b.y}`;
}

export function RiskGauge({ score, level, size = 240 }: { score: number; level: Level; size?: number }) {
  const { t, num } = useLang();
  const cx = 120;
  const cy = 120;
  const r = 96;
  const needle = polar(cx, cy, r - 22, Math.max(0, Math.min(score, 100)));
  const color = LEVEL_COLOR[level];

  return (
    <div className="flex flex-col items-center" style={{ width: size }}>
      <svg viewBox="0 0 240 140" width={size} role="img" aria-label={`${t("risk_level")}: ${score}/100`}>
        {BANDS.map((b) => (
          <path key={b.from} d={arc(cx, cy, r, b.from + 0.6, b.to - 0.6)} stroke={b.color} strokeWidth="20" fill="none" />
        ))}
        {score > 0 && <path d={arc(cx, cy, r, 0.6, Math.min(score, 99.4))} stroke={color} strokeWidth="20" fill="none" />}
        <line x1={cx} y1={cy} x2={needle.x} y2={needle.y} stroke="#15201a" strokeWidth="3" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r="7" fill="#15201a" />
        <text x="24" y="138" fontSize="11" fill="#5b675f" textAnchor="middle">{num(0)}</text>
        <text x="216" y="138" fontSize="11" fill="#5b675f" textAnchor="middle">{num(100)}</text>
      </svg>
      <div className="mt-1 text-center">
        <div className="text-5xl font-bold tabular-nums" style={{ color }}>
          {num(score)}
          <span className="text-xl font-medium text-muted">/{num(100)}</span>
        </div>
      </div>
    </div>
  );
}

export function LevelBadge({ level, large = false }: { level: Level; large?: boolean }) {
  const { t } = useLang();
  const styles: Record<Level, string> = {
    LOW: "bg-low-bg text-low border-low/30",
    MEDIUM: "bg-medium-bg text-medium border-medium/30",
    HIGH: "bg-high-bg text-high border-high/30",
  };
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border font-semibold ${styles[level]} ${
        large ? "px-4 py-1.5 text-base" : "px-2.5 py-0.5 text-xs"
      }`}
    >
      <span className="size-2 rounded-full" style={{ background: LEVEL_COLOR[level] }} />
      {t(`level_${level}`)}
    </span>
  );
}
