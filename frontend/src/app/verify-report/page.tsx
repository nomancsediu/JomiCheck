"use client";

import { QrCode } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useLang } from "@/lib/i18n";

export default function VerifyReportForm() {
  const { lang } = useLang();
  const router = useRouter();
  const [id, setId] = useState("");
  const [hash, setHash] = useState("");

  const cls = "w-full rounded-md border border-line bg-white px-3 py-2.5 font-mono text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100";

  return (
    <div className="page-x py-14 *:mx-auto *:max-w-xl">
      <div className="flex items-center gap-3">
        <span className="flex size-11 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
          <QrCode className="size-6" />
        </span>
        <h1 className="text-2xl font-bold tracking-tight">{lang === "bn" ? "রিপোর্টের সত্যতা যাচাই" : "Verify a report"}</h1>
      </div>
      <p className="mt-3 text-muted">
        {lang === "bn"
          ? "রিপোর্টের QR কোড স্ক্যান করুন, অথবা রিপোর্টে ছাপা আইডি ও SHA-256 হ্যাশ নিচে দিন।"
          : "Scan the QR code on the report, or enter the report ID and SHA-256 hash printed on it."}
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          router.push(`/verify-report/${id.trim().toUpperCase()}?h=${encodeURIComponent(hash.trim())}`);
        }}
        className="mt-8 space-y-4 rounded-xl border border-line bg-white p-6"
      >
        <label className="block text-sm font-medium">
          {lang === "bn" ? "রিপোর্ট আইডি" : "Report ID"}
          <input className={`${cls} mt-1.5`} value={id} onChange={(e) => setId(e.target.value)} placeholder="7F3A21C09B4E" required />
        </label>
        <label className="block text-sm font-medium">
          SHA-256
          <input className={`${cls} mt-1.5`} value={hash} onChange={(e) => setHash(e.target.value)} placeholder="e3b0c442…" required />
        </label>
        <button className="w-full rounded-md bg-brand-700 py-3 font-semibold text-white hover:bg-brand-800">
          {lang === "bn" ? "যাচাই করুন" : "Verify"}
        </button>
      </form>
    </div>
  );
}
