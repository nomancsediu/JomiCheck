"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { Suspense, useState } from "react";
import { Logo } from "./Logo";
import { useLang } from "@/lib/i18n";

function useLinks() {
  const { t } = useLang();
  return [
    { href: "/verify", label: t("nav_verify") },
    { href: "/upload", label: t("nav_upload") },
    { href: "/check-documents", label: t("nav_forgery") },
    { href: "/inheritance", label: t("nav_inheritance") },
    { href: "/costs", label: t("nav_costs") },
    { href: "/verify-report", label: t("nav_check_report") },
    { href: "/how-it-works", label: t("nav_how") },
  ];
}

function NavLinks({ withActive }: { withActive: boolean }) {
  const links = useLinks();
  return links.map((l) => <NavLink key={l.href} href={l.href} label={l.label} withActive={withActive} />);
}

function NavLink({ href, label, withActive }: { href: string; label: string; withActive: boolean }) {
  const cls = "whitespace-nowrap rounded-md px-2.5 py-2 text-sm font-medium transition-colors";
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
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="no-print sticky top-0 z-30 border-b border-line bg-white">
      <div className="page-x flex h-16 items-center gap-4">
        <Link href="/" className="flex min-w-0 items-center gap-3" onClick={() => setMenuOpen(false)}>
          <Logo />
          <span className="min-w-0 leading-tight">
            <span className="block text-lg font-bold tracking-tight text-brand-800">JomiCheck</span>
            <span className="block truncate text-xs text-muted">{t("brand_tagline")}</span>
          </span>
        </Link>

        <nav className="ml-auto hidden items-center gap-1 xl:flex">
          <Suspense fallback={<NavLinks withActive={false} />}>
            <NavLinks withActive />
          </Suspense>
        </nav>

        <div className="ml-auto flex shrink-0 items-center gap-2 xl:ml-2">
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
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="flex size-10 items-center justify-center rounded-md border border-line text-ink hover:bg-paper xl:hidden"
            aria-label={lang === "bn" ? "মেনু" : "Menu"}
            aria-expanded={menuOpen}
          >
            {menuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>
      {menuOpen && (
        <nav className="page-x flex flex-col gap-1 border-t border-line bg-white py-3 shadow-card xl:hidden">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setMenuOpen(false)}
              className="rounded-md px-3 py-3 font-medium text-ink hover:bg-paper"
            >
              {l.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
