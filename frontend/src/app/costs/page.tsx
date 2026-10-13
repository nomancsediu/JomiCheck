"use client";

import { AlertTriangle, Info, Receipt, Ruler } from "lucide-react";
import { use, useState } from "react";
import { api, type AreaType, type CostEstimate, type CostLine } from "@/lib/api";
import { useLang } from "@/lib/i18n";
import { AREA_UNITS, formatArea, formatTaka, fromAcre, toAcre } from "@/lib/units";

const AREA_TYPES: { key: AreaType; bn: string; en: string }[] = [
  { key: "union", bn: "ইউনিয়ন পরিষদ", en: "Union Parishad" },
  { key: "pourashava", bn: "পৌরসভা", en: "Pourashava (municipality)" },
  { key: "city_other", bn: "অন্যান্য সিটি কর্পোরেশন", en: "Other City Corporation" },
  { key: "city_major", bn: "ঢাকা, গাজীপুর, নারায়ণগঞ্জ, চট্টগ্রাম সিটি কর্পোরেশন", en: "Dhaka, Gazipur, Narayanganj, Chattogram City Corp." },
];

const cls = "rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-brand-500";

function CostTable({ title, lines, total }: { title: string; lines: CostLine[]; total: number }) {
  const { pick, num, lang } = useLang();
  return (
    <div>
      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">{title}</p>
      <table className="w-full text-sm">
        <tbody>
          {lines.map((l) => (
            <tr key={l.key} className="border-b border-line">
              <td className="py-2 pr-3">{pick(l.label)}</td>
              <td className="py-2 pr-3 text-right font-mono text-xs text-muted">{l.rate_percent ? `${num(l.rate_percent)}%` : ""}</td>
              <td className="py-2 text-right font-mono">{num(formatTaka(l.amount))}</td>
            </tr>
          ))}
          <tr>
            <td className="pt-2 font-semibold" colSpan={2}>
              {lang === "bn" ? "মোট" : "Total"}
            </td>
            <td className="pt-2 text-right font-mono font-semibold">{num(formatTaka(total))}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function CostCalculator({ initialArea, initialRate }: { initialArea: string; initialRate: string }) {
  const { lang, num, pick } = useLang();
  const [price, setPrice] = useState("");
  const [areaType, setAreaType] = useState<AreaType>("union");
  const [area, setArea] = useState(initialArea);
  const [areaUnit, setAreaUnit] = useState(initialArea ? "acre" : "decimal");
  const [ratePerDecimal, setRatePerDecimal] = useState(initialRate);
  const [result, setResult] = useState<CostEstimate | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const areaAcre = area ? toAcre(Number(area), areaUnit) : undefined;
    try {
      setResult(
        await api.costEstimate({
          price_bdt: Math.round(Number(price)),
          area_type: areaType,
          ...(areaAcre && ratePerDecimal
            ? { area_acre: areaAcre.toFixed(4), mouza_rate_per_acre: Math.round(Number(ratePerDecimal) * 100) }
            : {}),
        }),
      );
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
      <form onSubmit={submit} className="space-y-4 rounded-xl border border-line bg-white p-5">
        <label className="block text-sm font-medium">
          {lang === "bn" ? "জমির দাম (টাকা)" : "Land price (Tk)"}
          <input className={`${cls} mt-1.5 w-full`} type="number" min="0" step="1" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="1000000" required />
        </label>
        <label className="block text-sm font-medium">
          {lang === "bn" ? "জমির এলাকা" : "Where is the land?"}
          <select className={`${cls} mt-1.5 w-full`} value={areaType} onChange={(e) => setAreaType(e.target.value as AreaType)}>
            {AREA_TYPES.map((a) => (
              <option key={a.key} value={a.key}>
                {lang === "bn" ? a.bn : a.en}
              </option>
            ))}
          </select>
        </label>
        <fieldset className="rounded-lg border border-dashed border-line p-3">
          <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-muted">
            {lang === "bn" ? "মৌজা রেট যাচাই (ঐচ্ছিক)" : "Mouza rate check (optional)"}
          </legend>
          <div className="flex gap-2">
            <label className="block flex-1 text-sm font-medium">
              {lang === "bn" ? "জমির পরিমাণ" : "Area"}
              <input className={`${cls} mt-1.5 w-full`} type="number" min="0" step="any" value={area} onChange={(e) => setArea(e.target.value)} />
            </label>
            <label className="flex flex-col text-sm font-medium">
              {lang === "bn" ? "একক" : "Unit"}
              <select className={`${cls} mt-1.5`} value={areaUnit} onChange={(e) => setAreaUnit(e.target.value)}>
                {AREA_UNITS.slice(0, 4).map((u) => (
                  <option key={u.key} value={u.key}>
                    {pick(u.label)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="mt-3 block text-sm font-medium">
            {lang === "bn" ? "সরকারি মৌজা রেট (প্রতি শতাংশ, টাকা)" : "Government mouza rate (Tk per decimal)"}
            <input className={`${cls} mt-1.5 w-full`} type="number" min="0" step="1" value={ratePerDecimal} onChange={(e) => setRatePerDecimal(e.target.value)} />
          </label>
        </fieldset>
        {error && <p className="rounded-md bg-high-bg px-3 py-2 text-sm text-high">{error}</p>}
        <button className="w-full rounded-md bg-brand-700 py-2.5 font-semibold text-white hover:bg-brand-800">
          {lang === "bn" ? "খরচ হিসাব করুন" : "Estimate cost"}
        </button>
      </form>

      <section className="rounded-xl border border-line bg-white p-5">
        {result ? (
          <div className="space-y-5">
            {result.below_minimum && (
              <p className="flex gap-2 rounded-md border border-high/30 bg-high-bg px-3 py-2.5 text-sm text-high">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" /> {pick(result.notes[0])}
              </p>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-paper p-3">
                <p className="text-xs text-muted">{lang === "bn" ? "দলিল মূল্য (যার উপর ফি)" : "Deed value (fees based on)"}</p>
                <p className="mt-1 font-mono text-lg font-semibold">৳ {num(formatTaka(result.deed_value_bdt))}</p>
              </div>
              <div className="rounded-lg bg-brand-900 p-3 text-white">
                <p className="text-xs text-brand-100">{lang === "bn" ? "দামসহ সর্বমোট খরচ" : "Total incl. price"}</p>
                <p className="mt-1 font-mono text-lg font-semibold">৳ {num(formatTaka(result.grand_total))}</p>
              </div>
            </div>
            <CostTable title={lang === "bn" ? "রেজিস্ট্রেশন খরচ" : "Registration costs"} lines={result.registration} total={result.registration_total} />
            <CostTable title={lang === "bn" ? "নামজারি (মিউটেশন) ফি" : "Mutation fees"} lines={result.mutation} total={result.mutation_total} />
            <div className="space-y-1.5">
              {result.notes.slice(result.below_minimum ? 1 : 0).map((n) => (
                <p key={n.en} className="flex gap-2 text-xs text-muted">
                  <Info className="mt-0.5 size-3.5 shrink-0" /> {pick(n)}
                </p>
              ))}
            </div>
          </div>
        ) : (
          <p className="py-16 text-center text-sm text-muted">{lang === "bn" ? "ফলাফল এখানে দেখা যাবে।" : "Results will appear here."}</p>
        )}
      </section>
    </div>
  );
}

function UnitConverter() {
  const { lang, num, pick } = useLang();
  const [value, setValue] = useState("1");
  const [unit, setUnit] = useState("bigha");
  const acre = toAcre(Number(value) || 0, unit);

  return (
    <div className="rounded-xl border border-line bg-white p-5">
      <div className="flex flex-wrap gap-2">
        <input className={`${cls} w-40`} type="number" min="0" step="any" value={value} onChange={(e) => setValue(e.target.value)} aria-label="Value" />
        <select className={cls} value={unit} onChange={(e) => setUnit(e.target.value)} aria-label="Unit">
          {AREA_UNITS.map((u) => (
            <option key={u.key} value={u.key}>
              {pick(u.label)}
            </option>
          ))}
        </select>
      </div>
      <dl className="mt-4 grid gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
        {AREA_UNITS.map((u) => (
          <div key={u.key} className={`bg-white p-3 ${u.key === unit ? "bg-brand-50" : ""}`}>
            <dt className="text-xs text-muted">{pick(u.label)}</dt>
            <dd className="mt-0.5 font-mono text-base font-semibold">{num(formatArea(fromAcre(acre, u.key)))}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-xs text-muted">
        {lang === "bn"
          ? "১ কাঠা = ৭২০ বর্গফুট, ১ বিঘা = ২০ কাঠা ≈ ৩৩ শতাংশ, ১ একর = ১০০ শতাংশ। কিছু অঞ্চলে বিঘা ও কাঠার স্থানীয় মাপ ভিন্ন হয়; দলিলে লেখা একক মিলিয়ে নিন।"
          : "1 katha = 720 sq ft, 1 bigha = 20 katha ≈ 33 decimal, 1 acre = 100 decimal. Local bigha and katha sizes differ in some regions; match the unit written on the deed."}
      </p>
    </div>
  );
}

export default function CostsPage({ searchParams }: { searchParams: Promise<{ area?: string; rate?: string }> }) {
  const sp = use(searchParams);
  const { lang } = useLang();
  const initialArea = sp.area ?? "";
  const initialRate = sp.rate ? String(Math.round(Number(sp.rate) / 100)) : "";

  return (
    <div className="mx-auto max-w-6xl space-y-12 px-4 py-10 sm:px-6">
      <section>
        <div className="mb-6 flex items-center gap-3">
          <span className="flex size-11 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
            <Receipt className="size-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{lang === "bn" ? "জমি কেনার খরচ হিসাব" : "Land purchase cost estimate"}</h1>
            <p className="text-sm text-muted">
              {lang === "bn"
                ? "স্ট্যাম্প শুল্ক, রেজিস্ট্রেশন ফি, স্থানীয় সরকার কর, উৎস কর ও নামজারি ফি এক জায়গায়।"
                : "Stamp duty, registration fee, local government tax, source tax and mutation fees in one place."}
            </p>
          </div>
        </div>
        <CostCalculator initialArea={initialArea} initialRate={initialRate} />
      </section>

      <section>
        <div className="mb-4 flex items-center gap-3">
          <span className="flex size-11 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
            <Ruler className="size-6" />
          </span>
          <div>
            <h2 className="text-xl font-bold tracking-tight">{lang === "bn" ? "জমির একক রূপান্তর" : "Land unit converter"}</h2>
            <p className="text-sm text-muted">{lang === "bn" ? "শতাংশ, কাঠা, বিঘা, একর ও অন্যান্য একক।" : "Decimal, katha, bigha, acre and more."}</p>
          </div>
        </div>
        <UnitConverter />
      </section>
    </div>
  );
}
