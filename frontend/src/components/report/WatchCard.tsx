"use client";

import { Bell, BellRing, Loader2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type PlotWatch } from "@/lib/api";
import { useLang } from "@/lib/i18n";

export function WatchCard({ plotId, reportId }: { plotId: number; reportId: string }) {
  const { lang } = useLang();
  const bn = lang === "bn";
  const [watch, setWatch] = useState<PlotWatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .watches()
      .then((list) => setWatch(list.find((w) => w.plot_id === plotId) ?? null))
      .catch(() => setWatch(null))
      .finally(() => setLoading(false));
  }, [plotId]);

  async function toggle() {
    setBusy(true);
    try {
      if (watch) {
        await api.unwatch(watch.id);
        setWatch(null);
      } else {
        setWatch(await api.watch(plotId, reportId));
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="no-print rounded-xl border border-line bg-white p-5">
      <h2 className="flex items-center gap-2 font-semibold">
        {watch ? <BellRing className="size-5 text-brand-700" /> : <Bell className="size-5 text-brand-700" />}
        {bn ? "এই জমির উপর নজর রাখুন" : "Watch this plot"}
      </h2>
      <p className="mt-2 text-sm text-muted">
        {bn
          ? "বায়না থেকে রেজিস্ট্রি পর্যন্ত সময়ে নতুন দলিল, মামলা, বন্ধক, বায়নানামা বা অন্য ক্রেতা দেখা দিলে জমিচেক আপনাকে জানাবে।"
          : "Between the bainanama and registration, JomiCheck alerts you if a new deed, case, mortgage, bainanama or another buyer appears."}
      </p>
      {watch && (
        <p className="mt-3 text-sm">
          {watch.alerts.length > 0 ? (
            <span className="font-semibold text-high">
              {bn ? `${watch.alerts.length}টি নতুন সতর্কতা` : `${watch.alerts.length} new alert(s)`}
            </span>
          ) : (
            <span className="text-low">{bn ? "এখন পর্যন্ত কোনো পরিবর্তন নেই।" : "No changes so far."}</span>
          )}{" "}
          <Link href="/watch" className="font-semibold text-brand-700 hover:underline">
            {bn ? "নজরদারি তালিকা দেখুন →" : "Open watchlist →"}
          </Link>
        </p>
      )}
      <button
        onClick={toggle}
        disabled={loading || busy}
        className={`mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md py-2.5 text-sm font-semibold disabled:opacity-60 ${
          watch ? "border border-line bg-white text-ink hover:border-brand-500" : "bg-brand-700 text-white hover:bg-brand-800"
        }`}
      >
        {busy || loading ? <Loader2 className="size-4 animate-spin" /> : <Bell className="size-4" />}
        {watch ? (bn ? "নজর রাখা বন্ধ করুন" : "Stop watching") : bn ? "নজর রাখা শুরু করুন" : "Start watching"}
      </button>
    </section>
  );
}
