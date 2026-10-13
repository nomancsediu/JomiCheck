"use client";

import { ArrowUpRight, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { Logo } from "./Logo";
import { useLang } from "@/lib/i18n";

const REPO_URL = "https://github.com/nomancsediu/JomiCheck";

export function SiteFooter() {
  const { t, lang } = useLang();
  const bn = lang === "bn";

  const product = [
    { href: "/verify", label: t("nav_verify") },
    { href: "/upload", label: t("nav_upload") },
    { href: "/inheritance", label: t("nav_inheritance") },
    { href: "/costs", label: t("nav_costs") },
    { href: "/verify-report", label: t("nav_check_report") },
  ];
  const tech = [
    { name: "Gemma 4", note: bn ? "খতিয়ান পড়া ও প্রশ্নোত্তর" : "Document reading & Q&A" },
    { name: "Isolation Forest", note: bn ? "অস্বাভাবিক লেনদেন শনাক্ত" : "Unusual transfer detection" },
    { name: "Faraiz engine", note: bn ? "উত্তরাধিকার অংশ হিসাব" : "Inheritance shares" },
    { name: "SHA-256 + QR", note: bn ? "রিপোর্টের সত্যতা" : "Report integrity" },
  ];

  return (
    <footer className="no-print mt-20 bg-brand-900 text-brand-100">
      <div className="page-x grid gap-10 py-14 md:grid-cols-2 lg:grid-cols-[1.5fr_1fr_1.2fr_1fr]">
        <div>
          <Link href="/" className="inline-flex items-center gap-3">
            <Logo size={40} />
            <span className="leading-tight">
              <span className="block text-xl font-bold tracking-tight text-white">JomiCheck</span>
              <span className="block text-xs text-brand-200">{t("brand_tagline")}</span>
            </span>
          </Link>
          <p className="mt-5 max-w-sm text-sm leading-relaxed text-brand-100/90">
            {bn
              ? "জমি কেনার আগে মালিকানা, উত্তরাধিকার, নামজারি, মামলা ও প্রতারণার ঝুঁকি এক জায়গায় যাচাই করুন — আইনের ধারাসহ, সহজ বাংলায়।"
              : "Check ownership, inheritance, mutation, litigation and fraud risk in one place before buying land — with the law cited, in plain language."}
          </p>
          <p className="mt-5 inline-flex items-center gap-2 rounded-md border border-brand-700 px-3 py-1.5 text-xs text-brand-200">
            <ShieldCheck className="size-4" />
            {bn ? "শুধু কৃত্রিম (সিনথেটিক) ডেটা ব্যবহৃত" : "Synthetic data only"}
          </p>
        </div>

        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-brand-200">{bn ? "সেবা" : "Product"}</h3>
          <ul className="mt-4 space-y-2.5 text-sm">
            {product.map((l) => (
              <li key={l.href}>
                <Link href={l.href} className="text-brand-100 hover:text-white">
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-brand-200">{bn ? "প্রযুক্তি" : "Under the hood"}</h3>
          <ul className="mt-4 space-y-3 text-sm">
            {tech.map((item) => (
              <li key={item.name}>
                <span className="font-medium text-white">{item.name}</span>
                <span className="block text-xs text-brand-200">{item.note}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-brand-200">LandTech 2026</h3>
          <p className="mt-4 text-sm text-brand-100">
            {bn ? "সমস্যা বিবরণী" : "Problem statements"} <span className="font-mono text-white">P5 · P3 · P2</span>
          </p>
          <p className="mt-1 text-sm text-brand-200">
            {bn ? "ডিজিটাল ভূমি রেকর্ড, যাচাইকরণ ও ডিজিটাইজেশন" : "Digital Land Records, Verification & Digitization"}
          </p>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="mt-5 inline-flex items-center gap-1.5 rounded-md bg-white px-3 py-2 text-sm font-semibold text-brand-900 hover:bg-brand-50"
          >
            {bn ? "সোর্স কোড" : "Source code"} <ArrowUpRight className="size-4" />
          </a>
        </div>
      </div>

      <div className="border-t border-brand-800">
        <div className="page-x flex flex-col gap-3 py-6 text-xs text-brand-200 md:flex-row md:items-center md:justify-between">
          <p className="max-w-3xl">{t("disclaimer")}</p>
          <p className="shrink-0 text-sm">
            © {bn ? "২০২৬" : "2026"} JomiCheck · {bn ? "তৈরি করেছে" : "Built by"}{" "}
            <span className="font-semibold text-white">Team Semicolons</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
