"use client";

import {
  ArrowRight,
  Banknote,
  BrainCircuit,
  Baby,
  Building2,
  Copy,
  FileCheck2,
  FileScan,
  Gavel,
  GitBranch,
  Handshake,
  Landmark,
  QrCode,
  Receipt,
  Scale,
  ScrollText,
  Sparkles,
  TrendingDown,
  UserCheck,
  Users,
} from "lucide-react";
import Link from "next/link";
import { LevelBadge, RiskGauge } from "@/components/RiskGauge";
import { useLang } from "@/lib/i18n";

const CHECKS = [
  { icon: UserCheck, en: "Seller is the recorded owner", bn: "বিক্রেতা রেকর্ডভুক্ত মালিক কিনা", law: "Registration Act s.52A" },
  { icon: Copy, en: "Land already sold to someone else", bn: "জমি আগেই অন্যের কাছে বিক্রি হয়েছে কিনা", law: "Land Crime Act 2023" },
  { icon: Users, en: "Heir's Faraiz share vs. area sold", bn: "ওয়ারিশের ফারায়েজ অংশ বনাম বিক্রির পরিমাণ", law: "Muslim personal law" },
  { icon: FileCheck2, en: "Mutation (namjari) in seller's name", bn: "বিক্রেতার নামে নামজারি আছে কিনা", law: "Registration Act s.52A" },
  { icon: Landmark, en: "Khas, vested, waqf or forest land", bn: "খাস, অর্পিত, ওয়াকফ বা বনভূমি কিনা", law: "SAT Act 1950" },
  { icon: Building2, en: "Government acquisition notice", bn: "সরকারি অধিগ্রহণের নোটিশ", law: "ARIPA 2017" },
  { icon: Gavel, en: "Pending suits and injunctions", bn: "চলমান মামলা ও নিষেধাজ্ঞা", law: "CPC Order XXXIX" },
  { icon: Banknote, en: "Mortgage with a bank or lender", bn: "ব্যাংক বা অন্য কারো কাছে বন্ধক", law: "TP Act s.58" },
  { icon: Handshake, en: "Earlier bainanama with another buyer", bn: "অন্য ক্রেতার সাথে আগের বায়নানামা", law: "Registration Act s.17A" },
  { icon: ScrollText, en: "Power of attorney validity", bn: "আমমোক্তারনামার বৈধতা", law: "POA Act 2012" },
  { icon: GitBranch, en: "CS → SA → RS → BS survey lineage", bn: "সিএস → এসএ → আরএস → বিএস জরিপ ধারাবাহিকতা", law: "SAT Act s.145A" },
  { icon: Scale, en: "Pre-emption (Hak-e-Shufa) by co-sharers", bn: "শরিকদের অগ্রক্রয় (হক-শুফা)", law: "SAT Act s.96" },
  { icon: Baby, en: "Minor's share sold without court permission", bn: "আদালতের অনুমতি ছাড়া নাবালকের অংশ বিক্রি", law: "Guardians & Wards Act" },
  { icon: TrendingDown, en: "Rapid flips and under-priced deeds", bn: "দ্রুত হাতবদল ও কম দামের দলিল", law: "Fraud pattern" },
  { icon: Receipt, en: "Land development tax arrears", bn: "ভূমি উন্নয়ন কর বকেয়া", law: "LD Tax Act 2023" },
];

const STEPS = [
  { en: "Enter Dag, Khatian and seller", bn: "দাগ, খতিয়ান ও বিক্রেতার নাম দিন", body_en: "Pick District, Upazila and Mouza, then the plot and seller.", body_bn: "জেলা, উপজেলা ও মৌজা বেছে দাগ ও বিক্রেতার নাম দিন।" },
  { en: "Records are cross-checked", bn: "রেকর্ড মিলিয়ে দেখা হয়", body_en: "Khatians of every survey, deeds, mutation, cases, mortgages and tax.", body_bn: "সব জরিপের খতিয়ান, দলিল, নামজারি, মামলা, বন্ধক ও কর।" },
  { en: "Legal rules score the risk", bn: "আইনি নিয়মে ঝুঁকি নির্ণয়", body_en: "Each rule cites the law. Any critical issue means high risk.", body_bn: "প্রতিটি নিয়মের সাথে আইনের ধারা। গুরুতর সমস্যা থাকলেই উচ্চ ঝুঁকি।" },
  { en: "Get a sealed report", bn: "সিল করা রিপোর্ট পান", body_en: "Plain-language report with QR code, checklists and next steps.", body_bn: "QR কোডসহ সহজ ভাষার রিপোর্ট, চেকলিস্ট ও পরবর্তী পদক্ষেপ।" },
];

function SampleReport() {
  const { t, num, lang } = useLang();
  const rows = [
    { tier: "bg-high", en: "Seller is not the recorded owner", bn: "বিক্রেতা রেকর্ডভুক্ত মালিক নন", pts: 40 },
    { tier: "bg-high", en: "Land already sold to someone else", bn: "জমি আগেই অন্যের কাছে বিক্রি হয়েছে", pts: 35 },
    { tier: "bg-medium", en: "Conflicting transaction on record", bn: "সাংঘর্ষিক লেনদেন", pts: 10 },
    { tier: "bg-medium", en: "Land development tax unpaid", bn: "ভূমি উন্নয়ন কর বকেয়া", pts: 6 },
  ];
  return (
    <div className="rounded-xl border border-line bg-white shadow-[0_1px_0_#e2e6df,0_12px_32px_-12px_rgba(21,32,26,.18)]">
      <div className="flex items-center justify-between border-b border-line px-5 py-3 text-xs text-muted">
        <span className="font-mono">REPORT · 7F3A21C09B4E</span>
        <span>
          {t("plot")} {num(125)} · {lang === "bn" ? "রামপুর, সাভার" : "Rampur, Savar"}
        </span>
      </div>
      <div className="grid items-center gap-4 px-5 py-5 sm:grid-cols-[auto_1fr]">
        <RiskGauge score={91} level="HIGH" size={190} />
        <div>
          <LevelBadge level="HIGH" large />
          <p className="mt-3 text-sm text-muted">
            {lang === "bn"
              ? "গুরুতর ঝুঁকি পাওয়া গেছে। সরকারি যাচাই ও আইনি পরামর্শ ছাড়া এগোবেন না।"
              : "Serious risks found. Do not proceed without official verification and legal advice."}
          </p>
        </div>
      </div>
      <ul className="border-t border-line">
        {rows.map((r) => (
          <li key={r.en} className="flex items-center gap-3 border-b border-line px-5 py-2.5 text-sm last:border-b-0">
            <span className={`h-5 w-1 rounded-full ${r.tier}`} />
            <span className="flex-1">{lang === "bn" ? r.bn : r.en}</span>
            <span className="font-mono text-xs text-muted">+{num(r.pts)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

const TOOLS = [
  {
    icon: FileScan, href: "/upload",
    en: "Read a khatian photo", bn: "খতিয়ানের ছবি থেকে পড়া",
    body_en: "Upload a khatian or porcha. Gemma reads mouza, dag, owners and area in about 10 seconds and fills the form.",
    body_bn: "খতিয়ান বা পর্চার ছবি দিন। Gemma প্রায় ১০ সেকেন্ডে মৌজা, দাগ, মালিক ও পরিমাণ পড়ে ফর্ম পূরণ করে দেয়।",
    tag: "Gemma 4",
  },
  {
    icon: BrainCircuit, href: "/verify",
    en: "Machine-learning fraud signal", bn: "মেশিন লার্নিং দিয়ে প্রতারণা শনাক্ত",
    body_en: "An Isolation Forest model flags unusual sales — quick flips, brokers, chain transfers — that no single rule catches.",
    body_bn: "Isolation Forest মডেল অস্বাভাবিক বিক্রি ধরে — দ্রুত হাতবদল, দালাল, চেইন হস্তান্তর — যা একক কোনো নিয়মে ধরা পড়ে না।",
    tag: "Isolation Forest",
  },
  {
    icon: Sparkles, href: "/verify",
    en: "Ask about your report", bn: "রিপোর্ট নিয়ে প্রশ্ন করুন",
    body_en: "Ask in plain Bangla. Answers use only your report's facts and cite the law; nothing is invented.",
    body_bn: "সহজ বাংলায় প্রশ্ন করুন। উত্তর শুধু আপনার রিপোর্টের তথ্য ও আইন থেকে আসে; কিছু বানানো হয় না।",
    tag: "Gemma 4",
  },
  {
    icon: QrCode, href: "/verify-report",
    en: "Tamper-proof report", bn: "অপরিবর্তনযোগ্য রিপোর্ট",
    body_en: "Every report is sealed with SHA-256 and a QR code, so a bank or lawyer can confirm it was not edited.",
    body_bn: "প্রতিটি রিপোর্ট SHA-256 ও QR কোডে সিল করা, তাই ব্যাংক বা আইনজীবী যাচাই করতে পারেন যে এটি বদলানো হয়নি।",
    tag: "SHA-256",
  },
];

export default function Home() {
  const { t, lang, num } = useLang();

  return (
    <>
      <section className="border-b border-line bg-white">
        <div className="page-x grid items-center gap-12 py-14 lg:grid-cols-[1.1fr_1fr] lg:py-20">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-800">
              LandTech 2026 · P5 {lang === "bn" ? "নাগরিক ক্রয়-পূর্ব যাচাই" : "Citizen Pre-Purchase Verification"}
            </p>
            <h1 className="mt-5 text-4xl font-bold leading-tight tracking-tight text-ink sm:text-5xl">{t("hero_title")}</h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted">{t("hero_body")}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/verify"
                className="inline-flex items-center gap-2 rounded-md bg-brand-700 px-5 py-3 font-semibold text-white hover:bg-brand-800"
              >
                {t("start_verification")} <ArrowRight className="size-4" />
              </Link>
              <Link
                href="/upload"
                className="inline-flex items-center gap-2 rounded-md border border-line bg-white px-5 py-3 font-semibold text-ink hover:border-brand-500"
              >
                <FileScan className="size-4 text-brand-700" /> {t("upload_cta")}
              </Link>
            </div>
            <dl className="mt-10 grid max-w-lg grid-cols-3 divide-x divide-line border-y border-line">
              {[
                { n: "20+", k: "stat_checks" as const },
                { n: "5", k: "stat_surveys" as const },
                { n: "1", k: "stat_minutes" as const },
              ].map((s) => (
                <div key={s.k} className="px-4 py-4 first:pl-0">
                  <dt className="text-3xl font-bold text-brand-700">{num(s.n)}</dt>
                  <dd className="mt-1 text-sm text-muted">{t(s.k)}</dd>
                </div>
              ))}
            </dl>
          </div>
          <SampleReport />
        </div>
      </section>

      <section className="page-x py-16">
        <div className="max-w-2xl">
          <h2 className="text-3xl font-bold tracking-tight">{t("section_checks")}</h2>
          <p className="mt-2 text-muted">{t("section_checks_sub")}</p>
        </div>
        <div className="mt-8 grid gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-2 lg:grid-cols-3">
          {CHECKS.map((c) => (
            <div key={c.en} className="flex gap-4 bg-white p-5">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-brand-50 text-brand-700">
                <c.icon className="size-5" />
              </span>
              <div>
                <p className="font-semibold text-ink">{lang === "bn" ? c.bn : c.en}</p>
                <p className="mt-1 font-mono text-xs text-muted">{c.law}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="border-y border-line bg-brand-900 text-white">
        <div className="page-x py-16">
          <h2 className="text-3xl font-bold tracking-tight">{t("section_how")}</h2>
          <ol className="mt-10 grid gap-8 md:grid-cols-4">
            {STEPS.map((s, i) => (
              <li key={s.en} className="border-t-2 border-brand-500 pt-5">
                <span className="font-mono text-sm text-brand-200">{num(String(i + 1).padStart(2, "0"))}</span>
                <p className="mt-2 text-lg font-semibold">{lang === "bn" ? s.bn : s.en}</p>
                <p className="mt-2 text-sm text-brand-100">{lang === "bn" ? s.body_bn : s.body_en}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="page-x py-16">
        <div className="max-w-2xl">
          <h2 className="text-3xl font-bold tracking-tight">{t("section_tools")}</h2>
          <p className="mt-2 text-muted">{t("section_tools_sub")}</p>
        </div>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {TOOLS.map((tool) => (
            <Link
              key={tool.en}
              href={tool.href}
              className="group flex flex-col rounded-lg border border-line bg-white p-5 transition hover:border-brand-500 hover:shadow-sm"
            >
              <div className="flex items-center justify-between">
                <span className="flex size-10 items-center justify-center rounded-md bg-brand-50 text-brand-700">
                  <tool.icon className="size-5" />
                </span>
                <span className="rounded-full border border-line px-2 py-0.5 font-mono text-xs text-muted">{tool.tag}</span>
              </div>
              <h3 className="mt-4 font-semibold text-ink">{lang === "bn" ? tool.bn : tool.en}</h3>
              <p className="mt-1 flex-1 text-sm leading-relaxed text-muted">{lang === "bn" ? tool.body_bn : tool.body_en}</p>
              <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-brand-700">
                {lang === "bn" ? "খুলুন" : "Open"}
                <ArrowRight className="size-4 transition group-hover:translate-x-0.5" />
              </span>
            </Link>
          ))}
        </div>
      </section>
    </>
  );
}
