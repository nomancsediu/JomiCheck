"use client";

import { AlertTriangle } from "lucide-react";
import type { LineageStep } from "@/lib/api";
import { useLang } from "@/lib/i18n";

export function Lineage({ steps }: { steps: LineageStep[] }) {
  const { t, lang, num } = useLang();
  return (
    <ol className="flex flex-col gap-0 sm:flex-row sm:items-stretch">
      {steps.map((s, i) => {
        const broken = !s.consistent;
        return (
          <li key={`${s.survey}-${s.khatian_no}`} className="flex flex-1 flex-col sm:flex-row sm:items-center">
            {i > 0 && (
              <div className="flex items-center justify-center py-1 sm:px-1 sm:py-0">
                <span className={`h-5 w-0.5 sm:h-0.5 sm:w-5 ${broken ? "bg-high" : "bg-brand-200"}`} />
              </div>
            )}
            <div
              className={`flex-1 rounded-lg border p-3 ${
                broken ? "border-high/40 bg-high-bg" : "border-line bg-white"
              }`}
            >
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-mono text-sm font-semibold text-brand-800">{s.survey === "NAMJARI" ? (lang === "bn" ? "নামজারি" : "Mutation") : s.survey}</span>
                <span className="font-mono text-xs text-muted">{num(s.record_year)}</span>
              </div>
              <p className="mt-0.5 text-xs text-muted">
                {t("khatian_no")} {num(s.khatian_no)}
              </p>
              <ul className="mt-2 space-y-0.5 text-sm">
                {s.owners.map((o) => (
                  <li key={o.en} className="truncate" title={lang === "bn" ? o.bn : o.en}>
                    {lang === "bn" ? o.bn : o.en}
                  </li>
                ))}
              </ul>
              {broken && (
                <p className="mt-2 flex items-center gap-1 text-xs font-semibold text-high">
                  <AlertTriangle className="size-3.5" /> {t("lineage_break")}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
