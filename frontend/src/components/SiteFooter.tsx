"use client";

import Link from "next/link";
import { Logo } from "./Logo";
import { useLang } from "@/lib/i18n";

export function SiteFooter() {
  const { t, lang } = useLang();
  const bn = lang === "bn";
  const links = [
    { href: "/verify", label: t("nav_verify") },
    { href: "/upload", label: t("nav_upload") },
    { href: "/inheritance", label: t("nav_inheritance") },
    { href: "/costs", label: t("nav_costs") },
    { href: "/verify-report", label: t("nav_check_report") },
  ];

  return (
    <footer className="no-print mt-20 border-t border-line bg-white">
      <div className="page-x flex flex-col gap-6 py-10 lg:flex-row lg:items-center lg:justify-between">
        <Link href="/" className="flex items-center gap-3">
          <Logo size={36} />
          <span className="leading-tight">
            <span className="block font-bold tracking-tight text-brand-800">JomiCheck</span>
            <span className="block text-xs text-muted">{t("brand_tagline")}</span>
          </span>
        </Link>
        <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className="text-muted hover:text-brand-700">
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
      <div className="border-t border-line">
        <div className="page-x flex flex-col gap-2 py-5 text-xs text-muted md:flex-row md:items-center md:justify-between">
          <p className="max-w-3xl">{t("disclaimer")}</p>
          <p className="shrink-0 text-sm">
            © {bn ? "২০২৬" : "2026"} JomiCheck · {bn ? "তৈরি করেছে" : "Built by"}{" "}
            <span className="font-semibold text-brand-800">Team Semicolons</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
