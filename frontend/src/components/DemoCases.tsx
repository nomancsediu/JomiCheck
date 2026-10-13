"use client";

import { ArrowRight, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, buyerToken, type DemoCase } from "@/lib/api";
import { useLang } from "@/lib/i18n";

export function useDemoCases() {
  const [cases, setCases] = useState<DemoCase[] | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    api.demoCases().then(setCases).catch(() => setError(true));
  }, []);
  return { cases, error };
}

export function DemoCaseGrid() {
  const { cases, error } = useDemoCases();
  const { lang, t, num } = useLang();
  const router = useRouter();
  const [running, setRunning] = useState<string | null>(null);

  async function run(c: DemoCase) {
    setRunning(c.key);
    try {
      const report = await api.verify({
        mouza_id: c.mouza_id,
        dag_no: c.dag_no,
        seller_name: c.seller_name,
        area_acre: c.area_acre,
        khatian_no: c.khatian_no,
        buyer_token: buyerToken(),
      });
      router.push(`/report/${report.id}`);
    } catch {
      setRunning(null);
    }
  }

  if (error) return <p className="rounded-md border border-line bg-white p-4 text-sm text-muted">{t("backend_down")}</p>;
  if (!cases) return <p className="text-sm text-muted">{t("loading")}</p>;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cases.map((c, i) => (
        <button
          key={c.key}
          onClick={() => run(c)}
          disabled={running !== null}
          className="group flex flex-col rounded-lg border border-line bg-white p-5 text-left transition hover:border-brand-500 hover:shadow-sm disabled:opacity-60"
        >
          <div className="flex items-center justify-between text-xs text-muted">
            <span className="font-mono">#{num(String(i + 1).padStart(2, "0"))}</span>
            <span>
              {t("plot")} {num(c.dag_no)} · {lang === "bn" ? c.mouza_bn : c.mouza}
            </span>
          </div>
          <h3 className="mt-3 font-semibold text-ink">{lang === "bn" ? c.title_bn : c.title_en}</h3>
          <p className="mt-1 flex-1 text-sm text-muted">{lang === "bn" ? c.summary_bn : c.summary_en}</p>
          <div className="mt-4 flex items-center gap-2 text-sm font-semibold text-brand-700">
            {running === c.key ? <Loader2 className="size-4 animate-spin" /> : null}
            {running === c.key ? t("checking") : t("run_check")}
            {running !== c.key && <ArrowRight className="size-4 transition group-hover:translate-x-0.5" />}
          </div>
        </button>
      ))}
    </div>
  );
}
