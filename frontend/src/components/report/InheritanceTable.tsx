"use client";

import type { HeirRow } from "@/lib/api";
import { useLang } from "@/lib/i18n";

export const RELATION_LABEL: Record<string, { en: string; bn: string }> = {
  husband: { en: "Husband", bn: "স্বামী" },
  wife: { en: "Wife", bn: "স্ত্রী" },
  son: { en: "Son", bn: "ছেলে" },
  daughter: { en: "Daughter", bn: "মেয়ে" },
  father: { en: "Father", bn: "বাবা" },
  mother: { en: "Mother", bn: "মা" },
};

export function InheritanceTable({ heirs, highlightId }: { heirs: HeirRow[]; highlightId?: number }) {
  const { t, lang, num } = useLang();
  const max = Math.max(...heirs.map((h) => h.share_decimal), 0.0001);

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
          <th className="py-2 pr-3 font-medium">{t("heir")}</th>
          <th className="py-2 pr-3 font-medium">{t("relation")}</th>
          <th className="py-2 pr-3 font-medium">{t("share")}</th>
          <th className="w-2/5 py-2 font-medium">{t("acre")}</th>
        </tr>
      </thead>
      <tbody>
        {heirs.map((h, i) => {
          const name = typeof h.name === "string" ? h.name : lang === "bn" ? h.name.bn : h.name.en;
          const highlighted = highlightId !== undefined && h.person_id === highlightId;
          return (
            <tr key={i} className={`border-b border-line last:border-b-0 ${highlighted ? "bg-brand-50" : ""}`}>
              <td className="py-2.5 pr-3 font-medium">
                {name || "—"}
                {h.is_minor && (
                  <span className="ml-2 rounded bg-medium-bg px-1.5 py-0.5 text-xs text-medium">{t("minor")}</span>
                )}
              </td>
              <td className="py-2.5 pr-3 text-muted">{RELATION_LABEL[h.relation]?.[lang] ?? h.relation}</td>
              <td className="py-2.5 pr-3 font-mono">{num(h.share)}</td>
              <td className="py-2.5">
                <div className="flex items-center gap-3">
                  <div className="h-2 flex-1 rounded-full bg-paper">
                    <div className="h-2 rounded-full bg-brand-600" style={{ width: `${(h.share_decimal / max) * 100}%` }} />
                  </div>
                  <span className="w-16 text-right font-mono">{num(h.area_acre)}</span>
                </div>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
