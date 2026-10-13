"use client";

import { Logo } from "./Logo";
import { useLang } from "@/lib/i18n";

export function SiteFooter() {
  const { t, lang } = useLang();
  return (
    <footer className="no-print mt-20 border-t border-line bg-white">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1.4fr_1fr]">
        <div className="flex gap-4">
          <Logo size={32} />
          <div>
            <p className="font-semibold text-brand-800">JomiCheck</p>
            <p className="mt-1 max-w-xl text-sm text-muted">{t("disclaimer")}</p>
          </div>
        </div>
        <div className="text-sm text-muted md:text-right">
          <p>LandTech 2026 — {lang === "bn" ? "সমস্যা বিবরণী" : "Problem statement"} P5 · P3 · P2</p>
          <p className="mt-1">
            {lang === "bn"
              ? "ডিজিটাল ভূমি রেকর্ড, যাচাইকরণ ও ডিজিটাইজেশন"
              : "Digital Land Records, Verification & Digitization"}
          </p>
        </div>
      </div>
    </footer>
  );
}
