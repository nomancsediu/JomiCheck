"use client";

import { ShieldAlert, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { use, useEffect, useState } from "react";
import { LevelBadge } from "@/components/RiskGauge";
import { api, type ReportCheck } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const REASON = {
  match: {
    en: "This report matches the record in the JomiCheck registry. The details below are the original values.",
    bn: "এই রিপোর্টটি জমিচেক রেজিস্ট্রির রেকর্ডের সাথে মিলেছে। নিচের তথ্যগুলোই মূল তথ্য।",
  },
  hash_mismatch: {
    en: "The fingerprint (hash) does not match. The copy you have may have been altered. Compare it with the original values below.",
    bn: "ফিঙ্গারপ্রিন্ট (হ্যাশ) মেলেনি। আপনার কপিটি পরিবর্তিত হতে পারে। নিচের মূল তথ্যের সাথে মিলিয়ে দেখুন।",
  },
  registry_record_modified: {
    en: "The stored record no longer matches its seal. Do not rely on this report.",
    bn: "সংরক্ষিত রেকর্ড তার সিলের সাথে মিলছে না। এই রিপোর্টের ওপর নির্ভর করবেন না।",
  },
  not_found: {
    en: "No report with this ID exists. The document may be forged.",
    bn: "এই আইডির কোনো রিপোর্ট নেই। কাগজটি জাল হতে পারে।",
  },
};

export default function VerifyReportResult({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ h?: string }>;
}) {
  const { id } = use(params);
  const { h = "" } = use(searchParams);
  const { t, pick, num, lang } = useLang();
  const [check, setCheck] = useState<ReportCheck | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.checkReport(id, h).then(setCheck).catch(() => setError(true));
  }, [id, h]);

  if (error) return <p className="py-20 text-center text-muted">{t("backend_down")}</p>;
  if (!check) return <p className="py-20 text-center text-muted">{t("loading")}</p>;

  const ok = check.authentic;
  const facts = check.facts;

  return (
    <div className="page-x py-12 *:mx-auto *:max-w-3xl">
      <div className={`rounded-xl border-2 bg-white p-6 ${ok ? "border-low" : "border-high"}`}>
        <div className="flex items-start gap-4">
          {ok ? <ShieldCheck className="size-12 shrink-0 text-low" /> : <ShieldAlert className="size-12 shrink-0 text-high" />}
          <div>
            <h1 className={`text-2xl font-bold ${ok ? "text-low" : "text-high"}`}>
              {ok ? (lang === "bn" ? "রিপোর্টটি সঠিক" : "Authentic report") : lang === "bn" ? "রিপোর্টটি যাচাই হয়নি" : "Report could not be verified"}
            </h1>
            <p className="mt-2 text-ink/90">{REASON[check.reason][lang]}</p>
          </div>
        </div>
      </div>

      {facts && (
        <section className="mt-6 rounded-xl border border-line bg-white">
          <header className="border-b border-line px-5 py-3 font-semibold">
            {lang === "bn" ? "মূল রিপোর্টের তথ্য" : "Original report details"}
          </header>
          <dl className="divide-y divide-line text-sm">
            {[
              [t("report_id"), check.id],
              [t("generated"), check.created_at ? num(new Date(check.created_at).toLocaleString("en-GB")) : ""],
              [t("plot"), `${num(facts.plot.dag_no)}, ${pick(facts.plot.mouza)}, ${pick(facts.plot.upazila)}, ${pick(facts.plot.district)}`],
              [t("seller"), pick(facts.seller)],
              [t("area"), `${num(facts.area_acre)} ${t("acre")}`],
            ].map(([k, v]) => (
              <div key={k} className="grid grid-cols-[160px_1fr] gap-4 px-5 py-2.5">
                <dt className="text-muted">{k}</dt>
                <dd className="font-medium">{v}</dd>
              </div>
            ))}
            <div className="grid grid-cols-[160px_1fr] gap-4 px-5 py-2.5">
              <dt className="text-muted">{t("risk_level")}</dt>
              <dd className="flex items-center gap-3">
                <LevelBadge level={facts.level} /> <span className="font-mono">{num(facts.score)}/{num(100)}</span>
              </dd>
            </div>
            <div className="grid grid-cols-[160px_1fr] gap-4 px-5 py-2.5">
              <dt className="text-muted">{t("findings")}</dt>
              <dd>
                <ul className="list-disc space-y-0.5 pl-4">
                  {facts.flags.map((f) => (
                    <li key={f.en}>{pick(f)}</li>
                  ))}
                </ul>
              </dd>
            </div>
          </dl>
          <p className="break-all border-t border-line px-5 py-3 font-mono text-xs text-muted">SHA-256 {check.sha256}</p>
        </section>
      )}

      {ok && check.id && (
        <Link href={`/report/${check.id}`} className="mt-6 inline-block font-medium text-brand-700 hover:underline">
          {lang === "bn" ? "পূর্ণ রিপোর্ট দেখুন →" : "Open full report →"}
        </Link>
      )}
    </div>
  );
}
