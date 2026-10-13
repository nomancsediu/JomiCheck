"use client";

import { ShieldCheck } from "lucide-react";
import Link from "next/link";
import type { Report } from "@/lib/api";
import { useLang } from "@/lib/i18n";

export function IntegrityCard({ report }: { report: Report }) {
  const { t } = useLang();
  const path = new URL(report.verify_url).pathname + new URL(report.verify_url).search;

  return (
    <section className="print-avoid rounded-xl border border-line bg-white p-4">
      <div className="flex items-center gap-2">
        <ShieldCheck className="size-5 text-brand-700" />
        <h2 className="font-semibold">{t("integrity")}</h2>
      </div>
      <div className="mt-3 flex gap-4">
        <div
          className="size-28 shrink-0 rounded border border-line bg-white p-1 [&_svg]:h-full [&_svg]:w-full"
          dangerouslySetInnerHTML={{ __html: report.qr_svg }}
        />
        <div className="min-w-0 text-sm">
          <p className="text-muted">{t("integrity_body")}</p>
          <Link href={path} className="no-print mt-2 inline-block font-medium text-brand-700 hover:underline">
            {t("nav_check_report")} →
          </Link>
        </div>
      </div>
      <p className="mt-3 break-all rounded bg-paper px-2 py-1.5 font-mono text-xs leading-relaxed text-muted">
        SHA-256 {report.sha256}
      </p>
    </section>
  );
}
