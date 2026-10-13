"use client";

import { ChevronDown, Scale } from "lucide-react";
import { useState } from "react";
import type { Flag, Tier } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const TIER_STYLE: Record<Tier, { bar: string; chip: string }> = {
  CRITICAL: { bar: "bg-high", chip: "bg-high text-white" },
  MAJOR: { bar: "bg-medium", chip: "bg-medium-bg text-medium border border-medium/30" },
  MINOR: { bar: "bg-muted/50", chip: "bg-paper text-muted border border-line" },
};

export function FlagCard({ flag }: { flag: Flag }) {
  const { t, pick, num } = useLang();
  const [open, setOpen] = useState(false);
  const style = TIER_STYLE[flag.tier];

  return (
    <article className="print-avoid relative overflow-hidden rounded-lg border border-line bg-white">
      <span className={`absolute inset-y-0 left-0 w-1 ${style.bar}`} />
      <div className="px-5 py-4 pl-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded px-2 py-0.5 text-xs font-semibold ${style.chip}`}>{t(`tier_${flag.tier}`)}</span>
          <h3 className="flex-1 font-semibold text-ink">{pick(flag.title)}</h3>
          <span className="font-mono text-sm font-medium text-muted">+{num(flag.points)}</span>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-ink/90">{pick(flag.explanation)}</p>
        <div className="mt-3 grid gap-2 text-sm sm:grid-cols-[auto_1fr]">
          <span className="font-medium text-brand-800">{t("what_to_do")}:</span>
          <span className="text-ink/90">{pick(flag.action)}</span>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-1.5 rounded border border-line bg-paper px-2 py-1 font-mono text-xs text-muted">
            <Scale className="size-3.5" /> {flag.law}
          </span>
          {flag.evidence.length > 0 && (
            <button
              onClick={() => setOpen((o) => !o)}
              className="no-print inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:underline"
            >
              {t("evidence")} ({num(flag.evidence.length)})
              <ChevronDown className={`size-3.5 transition ${open ? "rotate-180" : ""}`} />
            </button>
          )}
        </div>
        {open && (
          <ul className="mt-3 space-y-1 rounded-md bg-paper p-3 font-mono text-xs text-muted">
            {flag.evidence.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}
