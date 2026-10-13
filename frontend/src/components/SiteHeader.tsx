"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense } from "react";
import { Logo } from "./Logo";
import { useLang } from "@/lib/i18n";
import { API_URL } from "@/lib/api";

const ADMIN_URL = API_URL.replace(/\/api\/?$/, "/admin/");

function useLinks() {
  const { t } = useLang();
  return [
    { href: "/verify", label: t("nav_verify") },
    { href: "/upload", label: t("nav_upload") },
    { href: "/inheritance", label: t("nav_inheritance") },
    { href: "/costs", label: t("nav_costs") },
    { href: "/verify-report", label: t("nav_check_report") },
  ];
}

function NavLinks({ withActive }: { withActive: boolean }) {
  const links = useLinks();
  return links.map((l) => <NavLink key={l.href} href={l.href} label={l.label} withActive={withActive} />);
}

function NavLink({ href, label, withActive }: { href: string; label: string; withActive: boolean }) {
  const cls = "rounded-md px-3 py-2 text-sm font-medium transition-colors";
  if (!withActive) {
    return (
      <Link href={href} className={`${cls} text-ink hover:bg-paper`}>
        {label}
      </Link>
    );
  }
  return <ActiveNavLink href={href} label={label} cls={cls} />;
}

function ActiveNavLink({ href, label, cls }: { href: string; label: string; cls: string }) {
  const pathname = usePathname();
  const active = pathname === href || pathname.startsWith(`${href}/`);
  return (
    <Link href={href} className={`${cls} ${active ? "bg-brand-50 text-brand-800" : "text-ink hover:bg-paper"}`}>
      {label}
    </Link>
  );
}

export function SiteHeader() {
  const { t, lang, setLang } = useLang();
  const links = useLinks();

  return (
    <header className="no-print sticky top-0 z-30 border-b border-line bg-white">
      <div className="page-x flex h-16 items-center gap-6">
        <Link href="/" className="flex items-center gap-3">
          <Logo />
          <span className="leading-tight">
            <span className="block text-lg font-bold tracking-tight text-brand-800">JomiCheck</span>
            <span className="block text-xs text-muted">{t("brand_tagline")}</span>
          </span>
        </Link>

        <nav className="ml-4 hidden items-center gap-1 md:flex">
          <Suspense fallback={<NavLinks withActive={false} />}>
            <NavLinks withActive />
          </Suspense>
          <a
            href={ADMIN_URL}
            target="_blank"
            rel="noreferrer"
            className="rounded-md px-3 py-2 text-sm font-medium text-muted hover:bg-paper hover:text-ink"
          >
            {t("nav_registry")}
          </a>
        </nav>

        <div className="ml-auto flex items-center gap-3">
          <div className="flex rounded-md border border-line p-0.5 text-sm" role="group" aria-label="Language">
            {(["bn", "en"] as const).map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                className={`rounded px-2.5 py-1 font-medium ${
                  lang === l ? "bg-brand-700 text-white" : "text-muted hover:text-ink"
                }`}
              >
                {l === "bn" ? "বাংলা" : "EN"}
              </button>
            ))}
          </div>
          <Link
            href="/verify"
            className="hidden rounded-md bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800 sm:block"
          >
            {t("start_verification")}
          </Link>
        </div>
      </div>
      <nav className="page-x flex gap-1 overflow-x-auto border-t border-line py-2 md:hidden">
        {links.map((l) => (
          <Link key={l.href} href={l.href} className="whitespace-nowrap rounded-md px-3 py-1.5 text-sm text-ink hover:bg-paper">
            {l.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
