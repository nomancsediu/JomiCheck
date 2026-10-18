"use client";

import { AlertTriangle, CheckCircle2, FileImage, FileSearch, Loader2, ScanText, Search, Upload, X, XCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { DocumentCheckCard } from "@/components/report/DocumentCheckCard";
import { api, buyerToken, type DocumentCheck, type DocumentFields, type ExtractedDocument } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const FILL_SAMPLES = [
  { files: ["khatian-rampur-101.png"], bn: "খতিয়ান · দাগ ১০১", en: "Khatian · Dag 101" },
  { files: ["khatian-rampur-118.png"], bn: "খতিয়ান · দাগ ১১৮", en: "Khatian · Dag 118" },
  { files: ["khatian-rampur-125.png"], bn: "খতিয়ান · দাগ ১২৫", en: "Khatian · Dag 125" },
];

const CHECK_SAMPLES = [
  {
    files: ["khatian-rampur-101.png", "deed-rampur-101.png"],
    bn: "আসল কাগজ · দাগ ১০১ (খতিয়ান ও দলিল)",
    en: "Genuine papers · Dag 101 (khatian and deed)",
  },
  {
    files: ["khatian-rampur-118-forged.png"],
    bn: "জাল খতিয়ান · দাগ ১১৮",
    en: "Forged khatian · Dag 118",
  },
  {
    files: ["khatian-rampur-125.png", "deed-rampur-125-forged.png", "dakhila-rampur-125-forged.png"],
    bn: "জাল দলিল ও দাখিলা · দাগ ১২৫",
    en: "Forged deed and dakhila · Dag 125",
  },
];

export type WorkspaceMode = "fill" | "check";

const MAX_DOCS = 5;
const ACCEPT = "image/jpeg,image/png,image/webp,application/pdf";
const cls = "w-full rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-brand-500";

type Item = {
  id: string;
  file: File;
  preview: string | null;
  status: "idle" | "reading" | "done" | "error";
  result?: ExtractedDocument;
  error?: string;
};

const isKhatian = (f: DocumentFields) => f.document_type === "khatian" || f.document_type === "mutation_khatian";

/** Pre-fill the form: a deed's buyer is the person now claiming the land, otherwise the khatian owner. */
function prefill(docs: DocumentFields[]) {
  const khatian = docs.find(isKhatian);
  const deed = docs.find((d) => d.document_type === "deed" && d.deed);
  const plot =
    deed?.plots.find((p) => p.found) ?? khatian?.plots.find((p) => p.found) ?? docs.flatMap((d) => d.plots)[0];
  return {
    seller: deed?.deed?.buyers[0] ?? khatian?.owners[0]?.name ?? "",
    dag: plot?.dag_no ?? "",
    khatian: khatian?.khatian_no ?? "",
    area: plot?.area_acre ?? "",
  };
}

/** "fill" reads papers to start a verification; "check" only compares papers with the records. */
export function DocumentWorkspace({ mode }: { mode: WorkspaceMode }) {
  const checking = mode === "check";
  const samples = checking ? CHECK_SAMPLES : FILL_SAMPLES;
  const { lang, num, pick, t } = useLang();
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [dragging, setDragging] = useState(false);
  const [reading, setReading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [check, setCheck] = useState<DocumentCheck | null>(null);
  const [form, setForm] = useState({ dag: "", khatian: "", seller: "", area: "" });
  const [showForm, setShowForm] = useState(!checking);
  const [elapsed, setElapsed] = useState(0);

  // Cache Components keeps this page alive after router.push; clear the progress state when it is hidden.
  useLayoutEffect(() => () => setVerifying(false), []);

  useEffect(() => {
    if (!reading) return;
    const started = Date.now();
    const id = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(id);
  }, [reading]);

  const bn = lang === "bn";
  const done = items.filter((i) => i.status === "done" && i.result);
  const docs = done.map((i) => i.result!.fields);
  const location = done.find((i) => i.result!.location)?.result!.location ?? null;
  const unread = items.some((i) => i.status === "idle" || i.status === "error");

  function add(files: File[], replace = false) {
    if (replace) items.forEach((i) => i.preview && URL.revokeObjectURL(i.preview));
    const fresh = files.map((file) => ({
      id: `${file.name}-${file.size}-${Math.random()}`,
      file,
      preview: file.type.startsWith("image/") ? URL.createObjectURL(file) : null,
      status: "idle" as const,
    }));
    setItems((prev) => [...(replace ? [] : prev), ...fresh].slice(0, MAX_DOCS));
    setCheck(null);
    setShowForm(!checking);
    setError(null);
  }

  function remove(id: string) {
    setItems((prev) => prev.filter((i) => i.id !== id));
    setCheck(null);
  }

  async function loadSet(files: string[]) {
    const loaded = await Promise.all(
      files.map(async (name) => {
        const blob = await fetch(`/samples/${name}`).then((r) => r.blob());
        return new File([blob], name, { type: blob.type || "image/png" });
      }),
    );
    add(loaded, true);
  }

  async function readAll() {
    setElapsed(0);
    setReading(true);
    setError(null);
    const results: ExtractedDocument[] = done.map((i) => i.result!);
    for (const item of items) {
      if (item.status === "done") continue;
      setItems((prev) => prev.map((i) => (i.id === item.id ? { ...i, status: "reading", error: undefined } : i)));
      try {
        const result = await api.extractDocument(item.file, lang);
        results.push(result);
        setItems((prev) => prev.map((i) => (i.id === item.id ? { ...i, status: "done", result } : i)));
      } catch (err) {
        const message = err instanceof Error ? err.message : t("error_generic");
        setItems((prev) => prev.map((i) => (i.id === item.id ? { ...i, status: "error", error: message } : i)));
      }
    }
    const fields = results.map((r) => r.fields);
    const next = prefill(fields);
    setForm(next);
    const loc = results.find((r) => r.location)?.location;
    if (checking && loc && fields.length) {
      try {
        setCheck(await api.checkDocuments(loc.mouza_id, fields, next.dag || undefined));
      } catch (err) {
        setError(err instanceof Error ? err.message : t("error_generic"));
      }
    }
    setReading(false);
  }

  async function verify(e: React.FormEvent) {
    e.preventDefault();
    if (!location) return;
    setVerifying(true);
    setError(null);
    try {
      const report = await api.verify({
        mouza_id: location.mouza_id,
        dag_no: form.dag.trim(),
        seller_name: form.seller.trim(),
        area_acre: form.area,
        khatian_no: form.khatian.trim(),
        buyer_token: buyerToken(),
        documents: docs,
      });
      router.push(`/report/${report.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error_generic"));
      setVerifying(false);
    }
  }

  function summary(f: DocumentFields) {
    if (f.document_type === "deed" && f.deed) {
      const parties = `${f.deed.sellers.join(", ")} → ${f.deed.buyers.join(", ")}`;
      return `${bn ? "দলিল" : "Deed"} ${num(f.deed.deed_no)} · ${parties}`;
    }
    if (f.document_type === "tax_receipt" && f.tax_receipt) {
      return `${bn ? "হোল্ডিং" : "Holding"} ${num(f.tax_receipt.holding_no)} · ${bn ? "পরিশোধ" : "paid to"} ${num(f.tax_receipt.paid_upto_year)}`;
    }
    const owners = f.owners.map((o) => o.name).join(", ");
    return `${f.survey ?? ""} ${bn ? "খতিয়ান" : "khatian"} ${num(f.khatian_no)}${owners ? ` · ${owners}` : ""}`.trim();
  }

  const owners = docs.find(isKhatian)?.owners ?? [];

  return (
    <div className="page-x py-10">
      <div className="flex items-center gap-3">
        <span className="hidden size-11 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700 sm:flex">
          {checking ? <FileSearch className="size-6" /> : <ScanText className="size-6" />}
        </span>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {checking ? (bn ? "জাল কাগজ শনাক্ত" : "Detect forged papers") : bn ? "ডকুমেন্ট আপলোড" : "Upload a document"}
          </h1>
          <p className="text-sm text-muted">
            {checking
              ? bn
                ? "বিক্রেতার দেওয়া খতিয়ান, দলিল ও খাজনার দাখিলা দিন। AI (Gemma) প্রতিটি পড়বে, আর জমিচেক সরকারি রেকর্ডের সাথে মিলিয়ে দেখাবে কোন কাগজ জাল হতে পারে।"
                : "Add the khatian, deed and land tax receipt the seller gave you. AI (Gemma) reads each one and JomiCheck compares them with the official record to show which papers may be forged."
              : bn
                ? "খতিয়ান বা পর্চার ছবি দিন। AI (Gemma) মৌজা, দাগ, মালিক ও পরিমাণ পড়ে ফর্ম পূরণ করে দেবে, তারপর পুরো যাচাই চালান।"
                : "Add a photo of the khatian or porcha. AI (Gemma) reads the mouza, dag, owners and area and fills the form, then run the full verification."}
          </p>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="min-w-0 space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              add(Array.from(e.dataTransfer.files));
            }}
            onClick={() => inputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed bg-white px-6 py-8 text-center transition-colors ${
              dragging ? "border-brand-600 bg-brand-50" : "border-line hover:border-brand-500"
            }`}
          >
            <Upload className="size-8 text-brand-700" />
            <p className="mt-3 font-medium">
              {bn ? "ফাইল টেনে আনুন বা ক্লিক করুন" : "Drop files here or click to choose"}
            </p>
            <p className="mt-1 text-xs text-muted">
              {checking
                ? bn
                  ? `খতিয়ান, দলিল, দাখিলা · সর্বোচ্চ ${num(MAX_DOCS)}টি · JPG, PNG, PDF`
                  : `Khatian, deed, dakhila · up to ${MAX_DOCS} · JPG, PNG, PDF`
                : bn
                  ? "খতিয়ান বা পর্চা · JPG, PNG, PDF"
                  : "Khatian or porcha · JPG, PNG, PDF"}
            </p>
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPT}
              multiple
              className="hidden"
              onChange={(e) => {
                add(Array.from(e.target.files ?? []));
                e.target.value = "";
              }}
            />
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">
              {checking ? (bn ? "নমুনা কাগজের সেট (কাল্পনিক)" : "Sample document sets (synthetic)") : bn ? "নমুনা খতিয়ান (কাল্পনিক)" : "Sample khatians (synthetic)"}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {samples.map((s) => (
                <button
                  key={s.en}
                  onClick={() => loadSet(s.files)}
                  className="inline-flex items-center gap-1.5 rounded-md border border-line bg-white px-3 py-1.5 text-xs font-medium hover:border-brand-500"
                >
                  <FileImage className="size-3.5 text-brand-700" /> {bn ? s.bn : s.en}
                </button>
              ))}
            </div>
          </div>

          {items.length > 0 && (
            <div className="space-y-2">
              {items.map((item) => (
                <div key={item.id} className="flex items-center gap-3 rounded-lg border border-line bg-white p-2.5">
                  {item.preview ? (
                    // eslint-disable-next-line @next/next/no-img-element -- local object URL preview
                    <img src={item.preview} alt="" className="size-14 shrink-0 rounded border border-line object-cover object-top" />
                  ) : (
                    <span className="flex size-14 shrink-0 items-center justify-center rounded border border-line text-xs text-muted">
                      PDF
                    </span>
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{item.file.name}</p>
                    <p className="truncate text-xs text-muted">
                      {item.status === "reading" && (bn ? "AI পড়ছে…" : "AI is reading…")}
                      {item.status === "idle" && (bn ? "পড়া হয়নি" : "Not read yet")}
                      {item.status === "error" && <span className="text-high">{item.error}</span>}
                      {item.status === "done" && item.result && summary(item.result.fields)}
                    </p>
                  </div>
                  {item.status === "reading" ? (
                    <Loader2 className="size-4 shrink-0 animate-spin text-brand-700" />
                  ) : item.status === "done" ? (
                    <CheckCircle2 className="size-4 shrink-0 text-low" />
                  ) : null}
                  <button
                    onClick={() => remove(item.id)}
                    disabled={reading}
                    aria-label={bn ? "সরান" : "Remove"}
                    className="rounded p-1 text-muted hover:bg-paper hover:text-ink disabled:opacity-40"
                  >
                    <X className="size-4" />
                  </button>
                </div>
              ))}
              {unread && (
                <button
                  onClick={readAll}
                  disabled={reading}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand-700 py-2.5 font-semibold text-white hover:bg-brand-800 disabled:opacity-60"
                >
                  {reading ? <Loader2 className="size-4 animate-spin" /> : <ScanText className="size-4" />}
                  {reading
                    ? `${bn ? "AI পড়ছে…" : "AI is reading…"} ${num(elapsed)}s`
                    : checking
                      ? bn
                        ? "পড়ুন ও রেকর্ডের সাথে মেলান"
                        : "Read and compare with records"
                      : bn
                        ? "AI দিয়ে পড়ুন"
                        : "Read with AI"}
                </button>
              )}
              {reading && (
                <p className="text-center text-xs text-muted">
                  {bn
                    ? "প্রতিটি কাগজ পড়তে সাধারণত ১০ থেকে ২০ সেকেন্ড লাগে।"
                    : "Each document usually takes 10 to 20 seconds."}
                </p>
              )}
            </div>
          )}

          <p className="text-xs text-muted">
            {bn
              ? "আপলোড করা ফাইল সংরক্ষণ করা হয় না। আসল ডকুমেন্টে ব্যক্তিগত তথ্য থাকলে আগে ঢেকে দিন।"
              : "Uploaded files are not stored. Cover personal details on real documents before uploading."}
          </p>
        </section>

        <section className="min-w-0 space-y-5 rounded-xl border border-line bg-white p-5">
          {error && (
            <p className="flex gap-2 rounded-md bg-high-bg px-3 py-2.5 text-sm text-high">
              <XCircle className="mt-0.5 size-4 shrink-0" /> {error}
            </p>
          )}
          {docs.length === 0 ? (
            <p className="py-20 text-center text-sm text-muted">
              {checking
                ? bn
                  ? "কাগজ পড়ার পর মিলিয়ে দেখার ফল এখানে দেখা যাবে।"
                  : "The comparison result will appear here after reading."
                : bn
                  ? "ডকুমেন্ট পড়ার পর তথ্য এখানে দেখা যাবে।"
                  : "The details will appear here after reading."}
            </p>
          ) : (
            <>
              {location ? (
                <p className="flex items-center gap-2 rounded-md bg-low-bg px-3 py-2 text-sm text-low">
                  <CheckCircle2 className="size-4 shrink-0" />
                  {bn ? "রেকর্ডে মৌজা পাওয়া গেছে:" : "Mouza found in records:"} {pick(location.mouza)} (JL {num(location.jl_no)})
                </p>
              ) : (
                <p className="flex items-center gap-2 rounded-md bg-medium-bg px-3 py-2 text-sm text-medium">
                  <AlertTriangle className="size-4 shrink-0" />
                  {bn ? "মৌজা রেকর্ডে মেলেনি।" : "Mouza not matched in records."}{" "}
                  <Link href="/verify" className="font-medium underline">
                    {bn ? "যাচাই ফর্মে নিজে বেছে নিন" : "Pick it on the verify form"}
                  </Link>
                </p>
              )}

              {check && (
                <div>
                  <h2 className="mb-2 font-semibold">{bn ? "কাগজ বনাম সরকারি রেকর্ড" : "Papers versus official record"}</h2>
                  <DocumentCheckCard check={check} names={done.map((i) => i.file.name)} />
                </div>
              )}

              {!showForm ? (
                <div className="space-y-3 border-t border-line pt-4">
                  <p className="text-sm text-muted">
                    {bn
                      ? "কাগজ ঠিক থাকলেও বিক্রেতার অধিকার, ওয়ারিশ, মামলা, বন্ধক ইত্যাদি যাচাই করা দরকার।"
                      : "Even if the papers match, the seller's right, heirs, cases, mortgages and more still need checking."}
                  </p>
                  <button
                    type="button"
                    onClick={() => setShowForm(true)}
                    disabled={!location || reading}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand-700 py-2.5 font-semibold text-white hover:bg-brand-800 disabled:opacity-50"
                  >
                    <Search className="size-4" />
                    {bn ? "এই কাগজ দিয়ে পুরো যাচাই করুন" : "Run the full verification with these papers"}
                  </button>
                </div>
              ) : (
              <form onSubmit={verify} className="space-y-3 border-t border-line pt-5">
                <h2 className="font-semibold">{bn ? "পুরো যাচাই চালান" : "Run the full verification"}</h2>
                <label className="block text-sm font-medium">
                  {t("seller_name")}
                  <input className={`${cls} mt-1.5`} value={form.seller} onChange={(e) => setForm({ ...form, seller: e.target.value })} required />
                </label>
                {owners.length > 1 && (
                  <div className="flex flex-wrap gap-1.5">
                    {owners.map((o) => (
                      <button
                        type="button"
                        key={o.name}
                        onClick={() => setForm({ ...form, seller: o.name })}
                        className={`rounded-full border px-2.5 py-1 text-xs ${form.seller === o.name ? "border-brand-600 bg-brand-50 text-brand-800" : "border-line"}`}
                      >
                        {o.name}
                        {o.share ? ` · ${o.share}` : ""}
                      </button>
                    ))}
                  </div>
                )}
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <label className="block text-sm font-medium">
                    {t("dag_no")}
                    <input className={`${cls} mt-1.5 font-mono`} value={form.dag} onChange={(e) => setForm({ ...form, dag: e.target.value })} required />
                  </label>
                  <label className="block text-sm font-medium">
                    {t("khatian_no")}
                    <input className={`${cls} mt-1.5 font-mono`} value={form.khatian} onChange={(e) => setForm({ ...form, khatian: e.target.value })} />
                  </label>
                  <label className="block text-sm font-medium">
                    {t("area")}
                    <input className={`${cls} mt-1.5 font-mono`} type="number" min="0.0001" step="0.0001" value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} required />
                  </label>
                </div>
                <button
                  disabled={!location || verifying || reading}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand-700 py-2.5 font-semibold text-white hover:bg-brand-800 disabled:opacity-50"
                >
                  {verifying ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
                  {bn ? "এই তথ্য দিয়ে যাচাই করুন" : "Verify with these details"}
                </button>
              </form>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}
