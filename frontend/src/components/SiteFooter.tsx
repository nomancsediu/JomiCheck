"use client";

import Link from "next/link";
import { Logo } from "./Logo";
import { useLang } from "@/lib/i18n";

export function SiteFooter() {
  const { t, lang } = useLang();
  const bn = lang === "bn";

  return (
    <footer className="no-print mt-20 border-t border-line bg-white">
      <div className="page-x flex flex-col gap-4 py-8 md:flex-row md:items-center md:justify-between">
        <Link href="/" className="flex items-center gap-3">
          <Logo size={32} />
          <span className="font-semibold text-brand-800">JomiCheck</span>
        </Link>
        <p className="text-sm text-muted">
          © {bn ? "২০২৬" : "2026"} · {bn ? "তৈরি করেছে" : "Built by"}{" "}
          <span className="font-semibold text-ink">Team Semicolons</span>
        </p>
      </div>
      <p className="page-x border-t border-line py-4 text-xs text-muted">{t("disclaimer")}</p>
    </footer>
  );
}
