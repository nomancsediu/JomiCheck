"use client";

import { AlertTriangle, CheckCircle2, FileImage, Loader2, ScanText, Search, Upload, XCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { api, buyerToken, type ExtractedDocument } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const SAMPLES = [
  { file: "/samples/khatian-rampur-101.png", bn: "নামজারি খতিয়ান · দাগ ১০১", en: "Mutation khatian · Dag 101" },
  { file: "/samples/khatian-rampur-118.png", bn: "বিএস খতিয়ান · দাগ ১১৮", en: "BS khatian · Dag 118" },
  { file: "/samples/khatian-rampur-125.png", bn: "খতিয়ান · দাগ ১২৫", en: "Khatian · Dag 125" },
];

const ACCEPT = "image/jpeg,image/png,image/webp,application/pdf";
const cls = "w-full rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-brand-500";

export default function UploadPage() {
  const { lang, num, pick, t } = useLang();
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [reading, setReading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [doc, setDoc] = useState<ExtractedDocument | null>(null);
  const [form, setForm] = useState({ dag: "", khatian: "", seller: "", area: "" });

  const bn = lang === "bn";

  function choose(f: File | undefined) {
    if (!f) return;
    if (preview) URL.revokeObjectURL(preview);
    setFile(f);
    setPreview(f.type.startsWith("image/") ? URL.createObjectURL(f) : null);
    setDoc(null);
    setError(null);
  }

  async function loadSample(path: string) {
    const blob = await fetch(path).then((r) => r.blob());
    choose(new File([blob], path.split("/").pop() ?? "sample.png", { type: blob.type || "image/png" }));
  }

  async function read() {
    if (!file) return;
    setReading(true);
    setError(null);
    try {
      const result = await api.extractDocument(file, lang);
      setDoc(result);
      const plot = result.fields.plots.find((p) => p.found) ?? result.fields.plots[0];
      setForm({
        dag: plot?.dag_no ?? "",
        khatian: result.fields.khatian_no,
        seller: result.fields.owners[0]?.name ?? "",
        area: plot?.area_acre ?? "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error_generic"));
    } finally {
      setReading(false);
    }
  }

  async function verify(e: React.FormEvent) {
    e.preventDefault();
    if (!doc?.location) return;
    setVerifying(true);
    setError(null);
    try {
      const report = await api.verify({
        mouza_id: doc.location.mouza_id,
        dag_no: form.dag.trim(),
        seller_name: form.seller.trim(),
        area_acre: form.area,
        khatian_no: form.khatian.trim(),
        buyer_token: buyerToken(),
      });
      router.push(`/report/${report.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error_generic"));
      setVerifying(false);
    }
  }

  const f = doc?.fields;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="flex items-center gap-3">
        <span className="flex size-11 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
          <ScanText className="size-6" />
        </span>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{bn ? "খতিয়ান বা পর্চা আপলোড করুন" : "Upload a khatian or porcha"}</h1>
          <p className="text-sm text-muted">
            {bn
              ? "AI (Gemma) ছবি পড়ে মৌজা, খতিয়ান, দাগ ও মালিকের তথ্য বের করবে। যাচাইয়ের আগে আপনি সব তথ্য ঠিক করে নিতে পারবেন।"
              : "AI (Gemma) reads the image and extracts mouza, khatian, dag and owner details. You can correct everything before verifying."}
          </p>
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              choose(e.dataTransfer.files[0]);
            }}
            onClick={() => inputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed bg-white px-6 py-10 text-center transition-colors ${
              dragging ? "border-brand-600 bg-brand-50" : "border-line hover:border-brand-500"
            }`}
          >
            <Upload className="size-8 text-brand-700" />
            <p className="mt-3 font-medium">{bn ? "ফাইল টেনে আনুন বা ক্লিক করুন" : "Drop a file here or click to choose"}</p>
            <p className="mt-1 text-xs text-muted">JPG, PNG, WEBP, PDF · {bn ? "সর্বোচ্চ ৮ MB" : "max 8 MB"}</p>
            <input ref={inputRef} type="file" accept={ACCEPT} className="hidden" onChange={(e) => choose(e.target.files?.[0])} />
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">{bn ? "নমুনা ডকুমেন্ট (কাল্পনিক)" : "Sample documents (synthetic)"}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {SAMPLES.map((s) => (
                <button
                  key={s.file}
                  onClick={() => loadSample(s.file)}
                  className="inline-flex items-center gap-1.5 rounded-md border border-line bg-white px-3 py-1.5 text-xs font-medium hover:border-brand-500"
                >
                  <FileImage className="size-3.5 text-brand-700" /> {bn ? s.bn : s.en}
                </button>
              ))}
            </div>
          </div>

          {file && (
            <div className="rounded-xl border border-line bg-white p-3">
              {preview ? (
                // eslint-disable-next-line @next/next/no-img-element -- local object URL preview
                <img src={preview} alt={file.name} className="max-h-[28rem] w-full rounded-md object-contain" />
              ) : (
                <p className="py-6 text-center text-sm text-muted">{file.name}</p>
              )}
              <button
                onClick={read}
                disabled={reading}
                className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand-700 py-2.5 font-semibold text-white hover:bg-brand-800 disabled:opacity-60"
              >
                {reading ? <Loader2 className="size-4 animate-spin" /> : <ScanText className="size-4" />}
                {reading ? (bn ? "AI পড়ছে…" : "AI is reading…") : bn ? "তথ্য বের করুন" : "Extract details"}
              </button>
            </div>
          )}

          <p className="text-xs text-muted">
            {bn
              ? "আপলোড করা ফাইল সংরক্ষণ করা হয় না। আসল ডকুমেন্টে ব্যক্তিগত তথ্য থাকলে আগে ঢেকে দিন।"
              : "Uploaded files are not stored. Cover personal details on real documents before uploading."}
          </p>
        </section>

        <section className="rounded-xl border border-line bg-white p-5">
          {error && (
            <p className="mb-4 flex gap-2 rounded-md bg-high-bg px-3 py-2.5 text-sm text-high">
              <XCircle className="mt-0.5 size-4 shrink-0" /> {error}
            </p>
          )}
          {!f ? (
            <p className="py-20 text-center text-sm text-muted">{bn ? "বের করা তথ্য এখানে দেখা যাবে।" : "Extracted details will appear here."}</p>
          ) : (
            <div className="space-y-5">
              <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
                {[
                  [bn ? "ডকুমেন্ট" : "Document", [f.survey, f.document_type].filter(Boolean).join(" · ")],
                  [t("district"), f.district],
                  [t("upazila"), f.upazila],
                  [t("mouza"), `${f.mouza}${f.jl_no ? ` · JL ${num(f.jl_no)}` : ""}`],
                  [t("ks_mutation_case"), f.mutation_case_no],
                ]
                  .filter(([, v]) => v)
                  .map(([k, v]) => (
                    <div key={k} className="flex justify-between gap-2 border-b border-dashed border-line py-1">
                      <span className="text-muted">{k}</span>
                      <span className="text-right font-medium">{v}</span>
                    </div>
                  ))}
              </div>

              {doc.location ? (
                <p className="flex items-center gap-2 rounded-md bg-low-bg px-3 py-2 text-sm text-low">
                  <CheckCircle2 className="size-4 shrink-0" />
                  {bn ? "রেকর্ডে মৌজা পাওয়া গেছে:" : "Mouza found in records:"} {pick(doc.location.mouza)} (JL {num(doc.location.jl_no)})
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

              {f.warnings.length > 0 && (
                <ul className="space-y-1 rounded-md border border-medium/30 bg-medium-bg px-3 py-2 text-xs text-medium">
                  {f.warnings.map((w) => (
                    <li key={w}>• {w}</li>
                  ))}
                </ul>
              )}

              <form onSubmit={verify} className="space-y-3">
                <label className="block text-sm font-medium">
                  {t("seller_name")}
                  <input className={`${cls} mt-1.5`} value={form.seller} onChange={(e) => setForm({ ...form, seller: e.target.value })} required />
                </label>
                {f.owners.length > 1 && (
                  <div className="flex flex-wrap gap-1.5">
                    {f.owners.map((o) => (
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
                <div className="grid grid-cols-3 gap-3">
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
                {f.plots.length > 0 && (
                  <p className="text-xs text-muted">
                    {bn ? "ডকুমেন্টে দাগ:" : "Dags on document:"}{" "}
                    {f.plots.map((p) => `${num(p.dag_no)}${p.found === false ? (bn ? " (রেকর্ডে নেই)" : " (not in records)") : ""}`).join(", ")}
                  </p>
                )}
                <button
                  disabled={!doc.location || verifying}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand-700 py-2.5 font-semibold text-white hover:bg-brand-800 disabled:opacity-50"
                >
                  {verifying ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
                  {bn ? "এই তথ্য দিয়ে যাচাই করুন" : "Verify with these details"}
                </button>
              </form>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
