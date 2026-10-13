"use client";

import { Banknote, FileText, Gavel, Handshake, Landmark, ScrollText, Stamp, Users } from "lucide-react";
import type { TimelineEvent } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const ICONS = {
  record: Landmark,
  inheritance: Users,
  deed: FileText,
  mutation: Stamp,
  legal: Gavel,
  mortgage: Banknote,
  agreement: Handshake,
  poa: ScrollText,
} as const;

const DOT: Record<TimelineEvent["status"], string> = {
  ok: "border-brand-200 bg-brand-50 text-brand-700",
  warning: "border-medium/40 bg-medium-bg text-medium",
  danger: "border-high/40 bg-high-bg text-high",
};

export function Timeline({ events }: { events: TimelineEvent[] }) {
  const { pick, num } = useLang();

  const fmt = (e: TimelineEvent) => (e.year_only ? num(e.date.slice(0, 4)) : num(e.date.split("-").reverse().join("-")));

  return (
    <ol className="relative space-y-5 border-l border-line pl-7">
      {events.map((e, i) => {
        const Icon = ICONS[e.kind];
        return (
          <li key={`${e.date}-${i}`} className="print-avoid relative">
            <span className={`absolute -left-[42px] flex size-7 items-center justify-center rounded-full border ${DOT[e.status]}`}>
              <Icon className="size-3.5" />
            </span>
            <p className="font-mono text-xs text-muted">{fmt(e)}</p>
            <p className={`mt-0.5 font-medium ${e.status === "danger" ? "text-high" : "text-ink"}`}>{pick(e.title)}</p>
            <p className="text-sm text-muted">{pick(e.detail)}</p>
          </li>
        );
      })}
    </ol>
  );
}
