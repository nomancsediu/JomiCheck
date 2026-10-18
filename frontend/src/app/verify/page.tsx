"use client";

import { AlertCircle, Check, Loader2, ScanText, Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useLayoutEffect, useMemo, useState } from "react";
import { useDemoCases } from "@/components/DemoCases";
import { ApiError, api, buyerToken, type DemoCase, type District } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const STEPS = [
  { en: "Reading record of rights (CS, SA, RS, BS)", bn: "খতিয়ান পড়া হচ্ছে (সিএস, এসএ, আরএস, বিএস)" },
  { en: "Matching seller with owners and heirs", bn: "বিক্রেতাকে মালিক ও ওয়ারিশদের সাথে মেলানো হচ্ছে" },
  { en: "Tracing deeds and mutation", bn: "দলিল ও নামজারি যাচাই হচ্ছে" },
  { en: "Checking cases, khas, acquisition, mortgage", bn: "মামলা, খাস, অধিগ্রহণ, বন্ধক দেখা হচ্ছে" },
  { en: "Scoring risk and sealing the report", bn: "ঝুঁকি নির্ণয় ও রিপোর্ট সিল করা হচ্ছে" },
];

type Form = {
  district: string;
  upazila: string;
  mouza: string;
  dag: string;
  khatian: string;
  seller: string;
  area: string;
};

const EMPTY: Form = { district: "", upazila: "", mouza: "", dag: "", khatian: "", seller: "", area: "" };

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="flex items-baseline justify-between text-sm font-medium text-ink">
        {label}
        {hint && <span className="text-xs font-normal text-muted">{hint}</span>}
      </span>
      <span className="mt-1.5 block">{children}</span>
    </label>
  );
}

const inputCls =
  "w-full rounded-md border border-line bg-white px-3 py-2.5 text-ink outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100 disabled:bg-paper disabled:text-muted";

export default function VerifyPage() {
  const { t, lang, pick, num } = useLang();
  const router = useRouter();
  const { cases, error: casesError } = useDemoCases();

  const [locations, setLocations] = useState<District[] | null>(null);
  const [plots, setPlots] = useState<{ dag_no: string; area_acre: string }[]>([]);
  const [form, setForm] = useState<Form>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.locations().then(setLocations).catch(() => setError(t("backend_down")));
  }, [t]);

  useEffect(() => {
    if (!form.mouza) return;
    let cancelled = false;
    api.plots(Number(form.mouza)).then((p) => !cancelled && setPlots(p)).catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [form.mouza]);

  // Cache Components keeps this page alive after router.push; clear the progress view when it is hidden.
  useLayoutEffect(
    () => () => {
      setLoading(false);
      setStep(0);
    },
    [],
  );

  useEffect(() => {
    if (!loading) return;
    const id = window.setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 380);
    return () => window.clearInterval(id);
  }, [loading]);

  const district = useMemo(() => locations?.find((d) => String(d.id) === form.district), [locations, form.district]);
  const upazila = useMemo(() => district?.upazilas.find((u) => String(u.id) === form.upazila), [district, form.upazila]);
  const plotArea = plots.find((p) => p.dag_no === form.dag)?.area_acre;

  const set = (key: keyof Form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const value = e.target.value;
    setForm((f) => {
      const next = { ...f, [key]: value };
      if (key === "district") Object.assign(next, { upazila: "", mouza: "", dag: "" });
      if (key === "upazila") Object.assign(next, { mouza: "", dag: "" });
      if (key === "mouza") next.dag = "";
      return next;
    });
    if (key === "district" || key === "upazila" || key === "mouza") setPlots([]);
    setError(null);
  };

  function fill(c: DemoCase) {
    setForm({
      district: String(c.district_id),
      upazila: String(c.upazila_id),
      mouza: String(c.mouza_id),
      dag: c.dag_no,
      khatian: c.khatian_no,
      seller: c.seller_name,
      area: c.area_acre,
    });
    setError(null);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setStep(0);
    setLoading(true);
    const started = Date.now();
    try {
      const report = await api.verify({
        mouza_id: Number(form.mouza),
        dag_no: form.dag.trim(),
        seller_name: form.seller.trim(),
        area_acre: form.area,
        khatian_no: form.khatian.trim(),
        buyer_token: buyerToken(),
      });
      const wait = Math.max(0, 1800 - (Date.now() - started));
      window.setTimeout(() => router.push(`/report/${report.id}`), wait);
    } catch (err) {
      setLoading(false);
      if (err instanceof ApiError && err.status === 404) {
        const body = err.body as { detail?: string; detail_bn?: string };
        setError(lang === "bn" ? body.detail_bn ?? err.message : body.detail ?? err.message);
      } else if (err instanceof ApiError) {
        setError(t("error_generic"));
      } else {
        setError(t("backend_down"));
      }
    }
  }

  const areaNum = Number(form.area);
  const canSubmit = form.mouza && form.dag.trim() && form.seller.trim() && areaNum > 0 && !loading;

  return (
    <div className="page-x py-10">
      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <section className="rounded-xl border border-line bg-white">
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-line px-6 py-5">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">{t("form_title")}</h1>
              <p className="mt-1 text-sm text-muted">{t("form_sub")}</p>
            </div>
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium hover:border-brand-500"
            >
              <ScanText className="size-4 text-brand-700" /> {t("upload_cta")}
            </Link>
          </div>

          {loading ? (
            <div className="px-6 py-10">
              <ul className="mx-auto max-w-md space-y-4">
                {STEPS.map((s, i) => (
                  <li key={s.en} className="flex items-center gap-3">
                    <span
                      className={`flex size-7 items-center justify-center rounded-full border ${
                        i < step
                          ? "border-brand-600 bg-brand-600 text-white"
                          : i === step
                            ? "border-brand-500 text-brand-600"
                            : "border-line text-muted"
                      }`}
                    >
                      {i < step ? <Check className="size-4" /> : i === step ? <Loader2 className="size-4 animate-spin" /> : null}
                    </span>
                    <span className={i <= step ? "text-ink" : "text-muted"}>{lang === "bn" ? s.bn : s.en}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <form onSubmit={submit} className="grid gap-5 px-6 py-6 sm:grid-cols-3">
              <Field label={t("district")}>
                <select className={inputCls} value={form.district} onChange={set("district")} required>
                  <option value="">{t("select")}</option>
                  {locations?.map((d) => (
                    <option key={d.id} value={d.id}>
                      {pick(d.name)}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label={t("upazila")}>
                <select className={inputCls} value={form.upazila} onChange={set("upazila")} disabled={!district} required>
                  <option value="">{t("select")}</option>
                  {district?.upazilas.map((u) => (
                    <option key={u.id} value={u.id}>
                      {pick(u.name)}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label={t("mouza")}>
                <select className={inputCls} value={form.mouza} onChange={set("mouza")} disabled={!upazila} required>
                  <option value="">{t("select")}</option>
                  {upazila?.mouzas.map((m) => (
                    <option key={m.id} value={m.id}>
                      {pick(m.name)} (JL {num(m.jl_no)})
                    </option>
                  ))}
                </select>
              </Field>

              <Field label={t("dag_no")} hint={plotArea ? `${t("total_area")}: ${num(plotArea)} ${t("acre")}` : undefined}>
                <input
                  className={inputCls}
                  value={form.dag}
                  onChange={set("dag")}
                  list="dag-options"
                  inputMode="numeric"
                  disabled={!form.mouza}
                  placeholder="125"
                  required
                />
                <datalist id="dag-options">
                  {plots.map((p) => (
                    <option key={p.dag_no} value={p.dag_no}>
                      {p.area_acre} acre
                    </option>
                  ))}
                </datalist>
              </Field>
              <Field label={t("khatian_no")} hint={t("optional")}>
                <input className={inputCls} value={form.khatian} onChange={set("khatian")} placeholder="456" />
              </Field>
              <Field
                label={t("area")}
                hint={areaNum > 0 ? `= ${num(+(areaNum * 100).toFixed(2))} ${t("decimal")}` : undefined}
              >
                <input
                  className={inputCls}
                  value={form.area}
                  onChange={set("area")}
                  type="number"
                  min="0.0001"
                  step="0.0001"
                  placeholder="0.30"
                  required
                />
              </Field>

              <div className="sm:col-span-3">
                <Field label={t("seller_name")} hint={t("seller_hint")}>
                  <input
                    className={inputCls}
                    value={form.seller}
                    onChange={set("seller")}
                    placeholder={lang === "bn" ? "যেমন: রহিম উদ্দিন" : "e.g. Rahim Uddin"}
                    required
                  />
                </Field>
              </div>

              {error && (
                <p className="flex items-center gap-2 rounded-md border border-high/30 bg-high-bg px-3 py-2 text-sm text-high sm:col-span-3">
                  <AlertCircle className="size-4 shrink-0" /> {error}
                </p>
              )}

              <div className="flex flex-col-reverse gap-4 border-t border-line pt-5 sm:col-span-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="max-w-md text-xs text-muted">{t("disclaimer")}</p>
                <button
                  type="submit"
                  disabled={!canSubmit}
                  className="inline-flex shrink-0 items-center justify-center gap-2 rounded-md bg-brand-700 px-5 py-3 font-semibold text-white hover:bg-brand-800 disabled:cursor-not-allowed disabled:bg-brand-200"
                >
                  <Search className="size-4" /> {t("run_check")}
                </button>
              </div>
            </form>
          )}
        </section>

        <aside className="no-print">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">{t("quick_fill")}</h2>
          {casesError && <p className="mt-3 text-sm text-high">{t("backend_down")}</p>}
          <ul className="mt-3 divide-y divide-line overflow-hidden rounded-xl border border-line bg-white">
            {cases?.map((c) => (
              <li key={c.key}>
                <button
                  onClick={() => fill(c)}
                  disabled={loading}
                  className="w-full px-4 py-3 text-left hover:bg-brand-50 disabled:opacity-60"
                >
                  <span className="block text-sm font-medium text-ink">{lang === "bn" ? c.title_bn : c.title_en}</span>
                  <span className="mt-0.5 block text-xs text-muted">
                    {t("plot")} {num(c.dag_no)} · {lang === "bn" ? c.mouza_bn : c.mouza} · {c.seller_name}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  );
}
