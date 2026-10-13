"use client";

import { AlertTriangle, CheckCircle2, FileSearch, XCircle } from "lucide-react";
import type { DocumentCheck } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const STATUS = {
  ok: { icon: CheckCircle2, text: "text-low", bg: "bg-low-bg", bn: "রেকর্ডের সাথে মেলে", en: "Matches the record" },
  major: { icon: AlertTriangle, text: "text-medium", bg: "bg-medium-bg", bn: "যাচাই করে নিন", en: "Needs checking" },
  critical: { icon: XCircle, text: "text-high", bg: "bg-high-bg", bn: "জাল হতে পারে", en: "Possibly forged" },
} as const;

export function DocumentCheckCard({ check, names }: { check: DocumentCheck; names?: string[] }) {
  const { lang, num } = useLang();
  const bn = lang === "bn";
  const forged = check.critical > 0;

  return (
    <div className="space-y-3">
      <p
        className={`flex items-start gap-2 rounded-lg px-4 py-3 text-sm font-semibold ${
          forged ? "bg-high-bg text-high" : check.major ? "bg-medium-bg text-medium" : "bg-low-bg text-low"
        }`}
      >
        <FileSearch className="mt-0.5 size-4 shrink-0" />
        {forged
          ? bn
            ? `${num(check.critical)}টি গুরুতর অমিল: ডকুমেন্ট সরকারি রেকর্ডের সাথে মেলে না।`
            : `${num(check.critical)} serious mismatch(es): documents do not match the official record.`
          : check.major
            ? bn
              ? "ডকুমেন্ট রেকর্ডে আছে, তবে কিছু তথ্য মিলিয়ে দেখুন।"
              : "Documents exist in the records, but some details need checking."
            : bn
              ? "সব ডকুমেন্ট সরকারি রেকর্ডের সাথে মেলে।"
              : "All documents match the official record."}
      </p>
      {check.documents.map((d) => {
        const s = STATUS[d.status];
        return (
          <div key={d.index} className="rounded-lg border border-line bg-white">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-2.5">
              <p className="min-w-0 text-sm font-semibold">
                {bn ? d.label.bn : d.label.en}
                {names?.[d.index] && <span className="ml-2 font-normal text-muted">{names[d.index]}</span>}
              </p>
              <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${s.bg} ${s.text}`}>
                <s.icon className="size-3.5" /> {bn ? s.bn : s.en}
              </span>
            </div>
            <ul className="space-y-1.5 px-4 py-3 text-sm">
              {d.checks.map((c, i) => {
                const Icon = STATUS[c.severity].icon;
                return (
                  <li key={i} className="flex items-start gap-2">
                    <Icon className={`mt-0.5 size-4 shrink-0 ${STATUS[c.severity].text}`} />
                    <span className={c.ok ? "text-muted" : "font-medium text-ink"}>{bn ? c.bn : c.en}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
