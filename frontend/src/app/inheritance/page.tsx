"use client";

import { Calculator, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { InheritanceTable, RELATION_LABEL } from "@/components/report/InheritanceTable";
import { api, type HeirRow } from "@/lib/api";
import { useLang } from "@/lib/i18n";

type Row = { relation: string; name: string };

const START: Row[] = [
  { relation: "wife", name: "" },
  { relation: "son", name: "" },
  { relation: "son", name: "" },
  { relation: "daughter", name: "" },
];

export default function InheritancePage() {
  const { lang, t, num } = useLang();
  const [area, setArea] = useState("1.00");
  const [rows, setRows] = useState<Row[]>(START);
  const [result, setResult] = useState<{ heirs: HeirRow[]; notes: string[]; law: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const update = (i: number, patch: Partial<Row>) => setRows((r) => r.map((row, j) => (j === i ? { ...row, ...patch } : row)));

  async function calculate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      setResult(await api.inheritance({ area_acre: area, heirs: rows }));
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : t("error_generic"));
    }
  }

  const cls = "rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-brand-500";

  return (
    <div className="page-x py-10">
      <div className="flex items-center gap-3">
        <span className="hidden size-11 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700 sm:flex">
          <Calculator className="size-6" />
        </span>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{lang === "bn" ? "ওয়ারিশ অংশ হিসাব (ফারায়েজ)" : "Inheritance share calculator (Faraiz)"}</h1>
          <p className="text-sm text-muted">
            {lang === "bn"
              ? "মৃত ব্যক্তির ওয়ারিশ যোগ করুন; প্রত্যেকে কতটুকু জমি পাবেন তা দেখুন।"
              : "Add the heirs of the deceased and see how much land each one inherits."}
          </p>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1.2fr]">
        <form onSubmit={calculate} className="space-y-4 rounded-xl border border-line bg-white p-5">
          <label className="block text-sm font-medium">
            {lang === "bn" ? "মোট জমি (একর)" : "Total land (acre)"}
            <input
              className={`${cls} mt-1.5 w-full`}
              type="number"
              min="0.0001"
              step="0.0001"
              value={area}
              onChange={(e) => setArea(e.target.value)}
              required
            />
          </label>
          <div>
            <p className="text-sm font-medium">{t("heir")}</p>
            <ul className="mt-1.5 space-y-2">
              {rows.map((row, i) => (
                <li key={i} className="flex gap-2">
                  <select className={cls} value={row.relation} onChange={(e) => update(i, { relation: e.target.value })}>
                    {Object.entries(RELATION_LABEL).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v[lang]}
                      </option>
                    ))}
                  </select>
                  <input
                    className={`${cls} min-w-0 flex-1`}
                    value={row.name}
                    onChange={(e) => update(i, { name: e.target.value })}
                    placeholder={lang === "bn" ? "নাম (ঐচ্ছিক)" : "Name (optional)"}
                  />
                  <button
                    type="button"
                    onClick={() => setRows((r) => r.filter((_, j) => j !== i))}
                    disabled={rows.length === 1}
                    className="rounded-md border border-line px-2.5 text-muted hover:text-high disabled:opacity-40"
                    aria-label="Remove"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </li>
              ))}
            </ul>
            <button
              type="button"
              onClick={() => setRows((r) => [...r, { relation: "son", name: "" }])}
              className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:underline"
            >
              <Plus className="size-4" /> {lang === "bn" ? "ওয়ারিশ যোগ করুন" : "Add heir"}
            </button>
          </div>
          {error && <p className="rounded-md bg-high-bg px-3 py-2 text-sm text-high">{error}</p>}
          <button className="w-full rounded-md bg-brand-700 py-2.5 font-semibold text-white hover:bg-brand-800">
            {lang === "bn" ? "হিসাব করুন" : "Calculate"}
          </button>
          <p className="text-xs text-muted">
            {lang === "bn"
              ? "স্বামী/স্ত্রী, ছেলে, মেয়ে, বাবা ও মা অন্তর্ভুক্ত। জটিল ক্ষেত্রে আইনজীবীর পরামর্শ নিন।"
              : "Covers spouse, sons, daughters, father and mother. Consult a lawyer for complex cases."}
          </p>
        </form>

        <section className="rounded-xl border border-line bg-white p-5">
          {result ? (
            <>
              <p className="mb-3 text-sm text-muted">
                {t("total_area")} {num(area)} {t("acre")} · {result.law}
              </p>
              <InheritanceTable heirs={result.heirs} />
              {result.notes.map((n) => (
                <p key={n} className="mt-3 rounded bg-paper px-3 py-2 text-xs text-muted">
                  {n}
                </p>
              ))}
            </>
          ) : (
            <p className="py-16 text-center text-sm text-muted">
              {lang === "bn" ? "ফলাফল এখানে দেখা যাবে।" : "Results will appear here."}
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
