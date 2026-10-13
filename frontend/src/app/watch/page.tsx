"use client";

import { AlertTriangle, BellRing, CheckCircle2, Loader2, XCircle } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type PlotWatch } from "@/lib/api";
import { useLang } from "@/lib/i18n";

export default function WatchPage() {
  const { lang, num, pick } = useLang();
  const bn = lang === "bn";
  const [watches, setWatches] = useState<PlotWatch[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = () =>
      api
        .watches()
        .then(setWatches)
        .catch((err) => setError(err instanceof Error ? err.message : "Error"));
    load();
    const id = window.setInterval(load, 15000);
    return () => window.clearInterval(id);
  }, []);

  async function stop(id: number) {
    await api.unwatch(id);
    setWatches((list) => list?.filter((w) => w.id !== id) ?? null);
  }

  return (
    <div className="page-x py-10">
      <div className="flex items-center gap-3">
        <span className="hidden size-11 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700 sm:flex">
          <BellRing className="size-6" />
        </span>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{bn ? "নজরদারি তালিকা" : "Watchlist"}</h1>
          <p className="text-sm text-muted">
            {bn
              ? "যেসব জমির উপর নজর রাখছেন, সেগুলোতে নজর রাখা শুরুর পর নতুন কিছু রেকর্ড হলে এখানে দেখা যাবে। তালিকাটি এই ব্রাউজারেই সংরক্ষিত।"
              : "Anything recorded on your watched plots after you started watching shows up here. The list is tied to this browser."}
          </p>
        </div>
      </div>

      <div className="mt-8 max-w-3xl space-y-4">
        {error && <p className="rounded-md bg-high-bg px-3 py-2.5 text-sm text-high">{error}</p>}
        {!watches && !error && <Loader2 className="size-6 animate-spin text-brand-700" />}
        {watches?.length === 0 && (
          <div className="rounded-xl border border-line bg-white p-6 text-sm text-muted">
            {bn
              ? "আপনি এখনো কোনো জমির উপর নজর রাখছেন না। যাচাই রিপোর্টে \"নজর রাখা শুরু করুন\" চাপুন।"
              : "You are not watching any plot yet. Press \"Start watching\" on a verification report."}{" "}
            <Link href="/verify" className="font-semibold text-brand-700 hover:underline">
              {bn ? "জমি যাচাই করুন →" : "Verify a plot →"}
            </Link>
          </div>
        )}
        {watches?.map((w) => (
          <section key={w.id} className="rounded-xl border border-line bg-white">
            <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
              <div className="min-w-0">
                <h2 className="font-semibold">
                  {bn ? "দাগ" : "Dag"} {num(w.plot.dag_no)}, {pick(w.plot.mouza)}, {pick(w.plot.upazila)}
                </h2>
                <p className="text-xs text-muted">
                  {bn ? "নজর রাখা শুরু:" : "Watching since"} {num(new Date(w.created_at).toLocaleDateString("en-GB"))}
                </p>
              </div>
              <div className="flex items-center gap-3 text-sm">
                {w.report_id && (
                  <Link href={`/report/${w.report_id}`} className="font-semibold text-brand-700 hover:underline">
                    {bn ? "রিপোর্ট" : "Report"}
                  </Link>
                )}
                <button onClick={() => stop(w.id)} className="text-muted hover:text-ink">
                  {bn ? "বন্ধ করুন" : "Stop"}
                </button>
              </div>
            </header>
            {w.alerts.length === 0 ? (
              <p className="flex items-center gap-2 px-5 py-4 text-sm text-low">
                <CheckCircle2 className="size-4" /> {bn ? "নজর রাখা শুরুর পর কোনো পরিবর্তন নেই।" : "No changes since you started watching."}
              </p>
            ) : (
              <ul className="divide-y divide-line">
                {w.alerts.map((a, i) => (
                  <li key={i} className="flex items-start gap-3 px-5 py-3 text-sm">
                    {a.severity === "critical" ? (
                      <XCircle className="mt-0.5 size-4 shrink-0 text-high" />
                    ) : (
                      <AlertTriangle className="mt-0.5 size-4 shrink-0 text-medium" />
                    )}
                    <span className="min-w-0">
                      <span className="font-medium">{bn ? a.bn : a.en}</span>
                      {a.date && <span className="ml-2 text-xs text-muted">{num(a.date)}</span>}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
        {watches && watches.some((w) => w.alerts.length > 0) && (
          <p className="rounded-lg border border-high/30 bg-high-bg px-4 py-3 text-sm text-high">
            {bn
              ? "নতুন কিছু রেকর্ড হলে টাকা দেওয়া বা রেজিস্ট্রি থামান এবং আবার যাচাই করুন।"
              : "If something new was recorded, pause payment or registration and verify again."}
          </p>
        )}
      </div>
    </div>
  );
}
