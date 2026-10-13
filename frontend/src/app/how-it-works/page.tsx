"use client";

import {
  BrainCircuit,
  Calculator,
  Database,
  FileScan,
  Gauge,
  type LucideIcon,
  MessageCircleQuestion,
  QrCode,
  Scale,
  ShieldAlert,
  UserSearch,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useLang } from "@/lib/i18n";

type Text = { bn: string; en: string };
type Rule = { check: Text; law: string; points: number };

const OVERVIEW: { icon: LucideIcon; title: Text }[] = [
  { icon: FileScan, title: { bn: "জমির তথ্য দিন", en: "Enter the land details" } },
  { icon: Database, title: { bn: "সব রেকর্ড একসাথে আনা হয়", en: "All records are collected" } },
  { icon: UserSearch, title: { bn: "বিক্রেতা কে, তা শনাক্ত", en: "The seller is identified" } },
  { icon: Scale, title: { bn: "২৪টি আইনি যাচাই", en: "24 legal checks run" } },
  { icon: Gauge, title: { bn: "ঝুঁকির স্কোর তৈরি", en: "A risk score is calculated" } },
  { icon: QrCode, title: { bn: "সিল করা রিপোর্ট", en: "A sealed report is issued" } },
];

const RECORDS: Text[] = [
  { bn: "সব জরিপের খতিয়ান: সিএস, এসএ, আরএস, বিএস এবং নামজারি খতিয়ান", en: "Khatians of every survey: CS, SA, RS, BS and the mutation khatian" },
  { bn: "রেজিস্ট্রি করা সব দলিল (বিক্রি, দান, হেবা)", en: "Every registered deed (sale, gift, heba)" },
  { bn: "নামজারি মামলা ও তার ফলাফল", en: "Mutation cases and their outcome" },
  { bn: "মালিকের মৃত্যু ও ওয়ারিশদের তথ্য", en: "Death of owners and their heirs" },
  { bn: "দেওয়ানি মামলা, ট্রাইব্যুনাল মামলা, ১৪৪ ধারা ও নিষেধাজ্ঞা", en: "Civil suits, tribunal cases, Section 144 orders and injunctions" },
  { bn: "ব্যাংক বন্ধক ও রেজিস্টার্ড বায়নানামা", en: "Bank mortgages and registered bainanama" },
  { bn: "আমমোক্তারনামা (পাওয়ার অব অ্যাটর্নি)", en: "Powers of attorney" },
  { bn: "খাস, অর্পিত, ওয়াকফ, বনভূমি ও অধিগ্রহণের তথ্য", en: "Khas, vested, waqf, forest and acquisition status" },
  { bn: "ভূমি উন্নয়ন কর (খাজনা) পরিশোধের অবস্থা", en: "Land development tax payment status" },
];

const ROLES: { role: Text; meaning: Text }[] = [
  { role: { bn: "রেকর্ডভুক্ত মালিক", en: "Recorded owner" }, meaning: { bn: "সর্বশেষ খতিয়ানে নাম আছে", en: "Named in the latest khatian" } },
  { role: { bn: "ওয়ারিশ", en: "Heir" }, meaning: { bn: "মৃত মালিকের উত্তরাধিকারী", en: "Heir of a deceased recorded owner" } },
  { role: { bn: "দলিলে ক্রেতা", en: "Deed buyer" }, meaning: { bn: "দলিলে কিনেছেন, খতিয়ানে নাম নাও থাকতে পারে", en: "Bought by deed; may not be in the khatian yet" } },
  { role: { bn: "আমমোক্তার", en: "Attorney" }, meaning: { bn: "মালিকের পক্ষে আমমোক্তারনামা আছে", en: "Holds a power of attorney from the owner" } },
  { role: { bn: "কোনো অধিকার নেই", en: "No right found" }, meaning: { bn: "কোনো রেকর্ডে বিক্রির অধিকার পাওয়া যায়নি", en: "No record gives this person a right to sell" } },
];

const CRITICAL: Rule[] = [
  { check: { bn: "বিক্রেতা রেকর্ডভুক্ত মালিক, ওয়ারিশ বা বৈধ ক্রেতা নন", en: "Seller is not the recorded owner, an heir or a lawful buyer" }, law: "Registration Act 1908, s.52A; Transfer of Property Act 1882", points: 40 },
  { check: { bn: "খতিয়ানের মালিক মারা গেছেন, অথচ তাঁর নামেই বিক্রি হচ্ছে", en: "The recorded owner has died but the land is sold in his name" }, law: "Succession law; Registration Act 1908, s.52A", points: 40 },
  { check: { bn: "জমি আগেই অন্য কারো কাছে দলিল করে বিক্রি হয়েছে", en: "The land was already sold to someone else by deed" }, law: "ভূমি অপরাধ প্রতিরোধ ও প্রতিকার আইন ২০২৩, ধারা ৪", points: 35 },
  { check: { bn: "খাস, অর্পিত, পরিত্যক্ত, ওয়াকফ, দেবোত্তর বা সংরক্ষিত বনভূমি", en: "Khas, vested, abandoned, waqf, debottor or reserved forest land" }, law: "SAT Act 1950; Vested Property Return Act 2001; Waqf Ordinance 1962; Forest Act 1927", points: 40 },
  { check: { bn: "সরকারি অধিগ্রহণের নোটিশ জারি হয়েছে", en: "A government acquisition notice has been issued" }, law: "Acquisition and Requisition of Immovable Property Act 2017", points: 40 },
  { check: { bn: "আদালত হস্তান্তরে নিষেধাজ্ঞা দিয়েছে", en: "A court order restrains transfer" }, law: "Code of Civil Procedure 1908, Order XXXIX", points: 40 },
  { check: { bn: "আমমোক্তারনামা বাতিল, অনিবন্ধিত, শুধু ব্যবস্থাপনার জন্য, অথবা মালিক মৃত", en: "Power of attorney is revoked, unregistered, management only, or the owner has died" }, law: "Power of Attorney Act 2012", points: 35 },
];

const MAJOR: Rule[] = [
  { check: { bn: "জমি নিয়ে মামলা চলছে", en: "A case about the land is pending" }, law: "Civil courts; SAT Act 1950, s.145A", points: 30 },
  { check: { bn: "সিএস থেকে বিএস পর্যন্ত মালিকানা হঠাৎ বদলেছে, কোনো দলিল বা উত্তরাধিকার ছাড়া", en: "Ownership changes between surveys with no deed or inheritance to explain it" }, law: "SAT Act 1950, s.145A (Land Survey Tribunal)", points: 30 },
  { check: { bn: "ওয়ারিশ নিজের ফারায়েজ অংশের চেয়ে বেশি জমি বিক্রি করছেন", en: "An heir is selling more than his Faraiz share" }, law: "ভূমি অপরাধ আইন ২০২৩; Muslim personal law (Faraiz)", points: 25 },
  { check: { bn: "নাবালকের অংশ আদালতের অনুমতি ছাড়া বিক্রি হচ্ছে", en: "A minor's share is sold without court permission" }, law: "Guardians and Wards Act 1890, s.29", points: 25 },
  { check: { bn: "জমি ব্যাংকে বন্ধক আছে", en: "The land is mortgaged" }, law: "Transfer of Property Act 1882, s.58", points: 25 },
  { check: { bn: "এক বছরের মধ্যে একই দাগ ৩ বা তার বেশিবার বিক্রি", en: "The same dag sold 3 or more times within one year" }, law: "Fraud pattern indicator", points: 25 },
  { check: { bn: "মেশিন লার্নিং মডেল লেনদেনের ধরনকে অস্বাভাবিক বলছে", en: "The machine learning model marks the transfer pattern as unusual" }, law: "Isolation Forest model; ভূমি সংস্কার আইন ২০২৩, ধারা ৫ (বেনামি লেনদেন)", points: 20 },
  { check: { bn: "বিক্রেতার নামে নামজারি হয়নি", en: "Mutation has not been done in the seller's name" }, law: "Registration Act 1908, s.52A; SAT Act 1950, s.143", points: 20 },
  { check: { bn: "অন্য ক্রেতার সাথে আগের রেজিস্টার্ড বায়নানামা আছে", en: "A registered bainanama with another buyer exists" }, law: "Registration Act 1908, s.17A; Specific Relief Act 1877", points: 20 },
];

const MINOR: Rule[] = [
  { check: { bn: "রেকর্ডে সাংঘর্ষিক লেনদেন আছে", en: "Conflicting transactions on record" }, law: "Transfer of Property Act 1882", points: 10 },
  { check: { bn: "শরিকরা অগ্রক্রয়ের (হক-শুফা) দাবি করতে পারেন", en: "Co-sharers can claim pre-emption (Hak-e-Shufa)" }, law: "SAT Act 1950, s.96", points: 10 },
  { check: { bn: "দেওয়া খতিয়ান নম্বর এই দাগের সাথে মেলে না", en: "The khatian number given does not match this dag" }, law: "Record of rights consistency", points: 10 },
  { check: { bn: "আগের বিক্রির দাম মৌজা রেটের অর্ধেকেরও কম", en: "A past sale was priced below half the mouza rate" }, law: "Mouza rate (minimum value) rules", points: 8 },
  { check: { bn: "ভূমি উন্নয়ন কর বকেয়া", en: "Land development tax is unpaid" }, law: "ভূমি উন্নয়ন কর আইন ২০২৩", points: 6 },
  { check: { bn: "বৈধ আমমোক্তারনামার মাধ্যমে বিক্রি (সতর্কতা)", en: "Sale through a valid power of attorney (caution)" }, law: "Power of Attorney Act 2012", points: 5 },
  { check: { bn: "গত ৩০ দিনে অন্য ক্রেতারাও এই দাগ যাচাই করেছেন", en: "Other buyers checked this dag in the last 30 days" }, law: "JomiCheck purchase intent alert", points: 5 },
  { check: { bn: "মৃত মালিক মুসলিম নন, তাই উত্তরাধিকার আইনজীবী দিয়ে যাচাই প্রয়োজন", en: "The deceased owner was not Muslim, so a lawyer must check the shares" }, law: "Hindu law (Dayabhaga) or other personal law", points: 5 },
];

const HEIRS: { name: Text; relation: Text; share: string; acre: string }[] = [
  { name: { bn: "ফাতেমা বেগম", en: "Fatema Begum" }, relation: { bn: "স্ত্রী", en: "Wife" }, share: "1/8", acre: "0.125" },
  { name: { bn: "করিম মিয়া", en: "Karim Mia" }, relation: { bn: "ছেলে", en: "Son" }, share: "7/20", acre: "0.35" },
  { name: { bn: "হাসান মিয়া", en: "Hasan Mia" }, relation: { bn: "ছেলে", en: "Son" }, share: "7/20", acre: "0.35" },
  { name: { bn: "রোকেয়া বেগম", en: "Rokeya Begum" }, relation: { bn: "মেয়ে", en: "Daughter" }, share: "7/40", acre: "0.175" },
];

const ML_FEATURES: Text[] = [
  { bn: "দলিলের দাম মৌজা রেটের কত অংশ", en: "Deed price as a share of the mouza rate" },
  { bn: "বিক্রেতা কত দিন জমির মালিক ছিলেন", en: "How many days the seller owned the land" },
  { bn: "এক বছরে এই দাগ কতবার বিক্রি হয়েছে", en: "How many times this dag was sold in one year" },
  { bn: "দাগের কত অংশ বিক্রি হচ্ছে", en: "What share of the dag is being sold" },
  { bn: "বিক্রেতা এক বছরে কয়টি ভিন্ন দাগ বিক্রি করেছেন", en: "How many different dags the seller sold in one year" },
];

const REPORT_PARTS: Text[] = [
  { bn: "ঝুঁকির মাত্রা ও স্কোর, সহজ ভাষায় সারাংশ", en: "Risk level and score with a plain language summary" },
  { bn: "প্রতিটি সমস্যা: কী পাওয়া গেছে, কোন আইন, কী করবেন", en: "Each finding: what was found, which law, what to do" },
  { bn: "সর্বশেষ খতিয়ান সরকারি কলাম বিন্যাসে", en: "The latest khatian in the official column layout" },
  { bn: "ওয়ারিশদের ফারায়েজ অংশ ও জরিপের ধারাবাহিকতা", en: "Heirs' Faraiz shares and the survey lineage" },
  { bn: "মালিকানার পূর্ণ ইতিহাস", en: "Full ownership timeline" },
  { bn: "যে কাগজ চাইবেন, বিক্রেতাকে যে প্রশ্ন করবেন, সরেজমিনে যা দেখবেন", en: "Documents to ask for, questions for the seller, what to check on site" },
];

function Step({ n, icon: Icon, title, children }: { n: number; icon: LucideIcon; title: string; children: ReactNode }) {
  const { num, t } = useLang();
  return (
    <section className="grid gap-6 border-t border-line py-10 lg:grid-cols-[260px_1fr]">
      <div className="flex items-start gap-4 lg:flex-col">
        <span className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-brand-700 text-white">
          <Icon className="size-6" />
        </span>
        <div>
          <p className="font-mono text-sm text-brand-700">
            {t("hiw_step")} {num(String(n).padStart(2, "0"))}
          </p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight">{title}</h2>
        </div>
      </div>
      <div className="space-y-4 leading-relaxed text-ink/90">{children}</div>
    </section>
  );
}

function NumberedList({ items }: { items: string[] }) {
  const { num } = useLang();
  return (
    <ol className="space-y-2">
      {items.map((item, i) => (
        <li key={item} className="flex gap-3">
          <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-bold text-brand-800">
            {num(i + 1)}
          </span>
          <span>{item}</span>
        </li>
      ))}
    </ol>
  );
}

function RuleTable({ title, note, rules, tone }: { title: string; note: string; rules: Rule[]; tone: string }) {
  const { lang, num } = useLang();
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-white">
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-line px-5 py-3">
        <h3 className="flex items-center gap-2 font-bold">
          <span className={`h-4 w-1.5 rounded-full ${tone}`} />
          {title}
        </h3>
        <p className="text-sm text-muted">{note}</p>
      </div>
      <table className="w-full text-left text-sm">
        <thead className="bg-paper text-xs text-muted">
          <tr>
            <th className="px-5 py-2 font-semibold">{lang === "bn" ? "কী যাচাই হয়" : "What is checked"}</th>
            <th className="px-5 py-2 font-semibold">{lang === "bn" ? "আইনি ভিত্তি" : "Legal basis"}</th>
            <th className="px-5 py-2 text-right font-semibold">{lang === "bn" ? "পয়েন্ট" : "Points"}</th>
          </tr>
        </thead>
        <tbody>
          {rules.map((r) => (
            <tr key={r.check.en} className="border-t border-line align-top">
              <td className="px-5 py-3 font-medium text-ink">{r.check[lang]}</td>
              <td className="px-5 py-3 text-muted">{r.law}</td>
              <td className="px-5 py-3 text-right font-mono font-semibold">+{num(r.points)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function HowItWorks() {
  const { lang, num, t } = useLang();
  const bn = lang === "bn";
  const L = (text: Text) => text[lang];

  return (
    <div className="page-x py-12">
      <header className="max-w-3xl">
        <h1 className="text-4xl font-bold tracking-tight">{t("hiw_title")}</h1>
        <p className="mt-4 text-lg leading-relaxed text-muted">
          {bn
            ? "একজন অভিজ্ঞ ভূমি আইনজীবী জমি কেনার আগে যেসব কাগজ ও আইন দেখেন, JomiCheck সেগুলো ধাপে ধাপে স্বয়ংক্রিয়ভাবে যাচাই করে। প্রতিটি সিদ্ধান্তের পেছনে বাংলাদেশের নির্দিষ্ট আইনের ধারা আছে, আর রিপোর্টে তা স্পষ্টভাবে লেখা থাকে।"
            : "JomiCheck checks, step by step, the papers and laws an experienced land lawyer reviews before a purchase. Every decision is tied to a specific section of Bangladeshi law, and the report states it clearly."}
        </p>
      </header>

      <ol className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
        {OVERVIEW.map((s, i) => (
          <li key={s.title.en} className="rounded-xl border border-line bg-white p-4">
            <div className="flex items-center justify-between">
              <s.icon className="size-5 text-brand-700" />
              <span className="font-mono text-sm font-semibold text-muted">{num(String(i + 1).padStart(2, "0"))}</span>
            </div>
            <p className="mt-3 font-semibold leading-snug">{L(s.title)}</p>
          </li>
        ))}
      </ol>

      <div className="mt-12">
        <Step n={1} icon={FileScan} title={L({ bn: "জমির তথ্য দেওয়া", en: "Entering the land details" })}>
          <p>
            {bn
              ? "ক্রেতা জেলা, উপজেলা, মৌজা, দাগ নম্বর, বিক্রেতার নাম এবং কতটুকু জমি কিনবেন তা দেন। খতিয়ান নম্বর ঐচ্ছিক।"
              : "The buyer selects the district, upazila and mouza, then enters the dag number, the seller's name and the area to buy. The khatian number is optional."}
          </p>
          <p>
            {bn
              ? "চাইলে টাইপ না করে খতিয়ান বা পর্চার ছবি বা PDF আপলোড করা যায়। Google AI Studio থেকে Gemma 4 মডেল ছবিটি পড়ে মৌজা, জেএল নম্বর, খতিয়ান নম্বর, মালিকের নাম, পিতার নাম, অংশ, দাগ ও জমির পরিমাণ বের করে, এবং আমাদের রেকর্ডের সাথে মৌজা ও দাগ মিলিয়ে দেখে। ক্রেতা সব ঘর দেখে ঠিক করে নিতে পারেন। ফাইল কোথাও সংরক্ষণ করা হয় না।"
              : "Instead of typing, the buyer can upload a photo or PDF of the khatian. The Gemma 4 model from Google AI Studio reads the mouza, JL number, khatian number, owners, fathers' names, shares, dag and area, then matches the mouza and dag with our records. The buyer reviews and corrects every field. The file is never stored."}
          </p>
          <Link href="/upload" className="inline-flex font-semibold text-brand-700 hover:underline">
            {bn ? "ডকুমেন্ট আপলোড পেজ খুলুন →" : "Open the document upload page →"}
          </Link>
        </Step>

        <Step n={2} icon={Database} title={L({ bn: "সব রেকর্ড একসাথে আনা", en: "Collecting every record" })}>
          <p>
            {bn
              ? "দাগ নম্বর দিয়ে ওই জমির সাথে জড়িত সব রেকর্ড একসাথে আনা হয়:"
              : "Using the dag number, every record linked to that plot is brought together:"}
          </p>
          <NumberedList items={RECORDS.map(L)} />
          <p className="rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-900">
            {bn
              ? "হ্যাকাথনের নিয়ম মেনে এই প্রোটোটাইপের সব রেকর্ড কৃত্রিম (সিনথেটিক)। কোনো সরকারি পোর্টাল থেকে তথ্য স্ক্র্যাপ বা ডাউনলোড করা হয়নি, এবং কোনো আসল ব্যক্তির তথ্য নেই।"
              : "Following the hackathon rules, every record in this prototype is synthetic. Nothing was scraped or downloaded from any government portal, and no real person's data is used."}
          </p>
        </Step>

        <Step n={3} icon={UserSearch} title={L({ bn: "বিক্রেতা কে, তা শনাক্ত করা", en: "Identifying the seller" })}>
          <p>
            {bn
              ? "বিক্রেতার নাম বাংলা বা ইংরেজি যেভাবেই লেখা হোক, RapidFuzz দিয়ে বানান মিলিয়ে দেখা হয় (কমপক্ষে ৮৫% মিল লাগে), যেমন \"করিম মিয়া\" আর \"Karim Mia\" একই ব্যক্তি। তারপর রেকর্ড দেখে ঠিক করা হয় বিক্রেতার জমির উপর কী অধিকার আছে:"
              : "Whether the seller's name is written in Bangla or English, it is fuzzy matched with RapidFuzz (at least 85% similarity), so \"করিম মিয়া\" and \"Karim Mia\" are the same person. The records then decide what right the seller has:"}
          </p>
          <div className="overflow-hidden rounded-xl border border-line bg-white">
            <table className="w-full text-left text-sm">
              <tbody>
                {ROLES.map((r) => (
                  <tr key={r.role.en} className="border-t border-line first:border-t-0">
                    <td className="w-48 px-5 py-3 font-semibold">{L(r.role)}</td>
                    <td className="px-5 py-3 text-muted">{L(r.meaning)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>
            {bn
              ? "এই ভূমিকার উপর নির্ভর করে পরের ধাপে কোন আইন প্রযোজ্য হবে। যেমন ওয়ারিশ হলে ফারায়েজ হিসাব হয়, দলিলে ক্রেতা হলে নামজারি দেখা হয়।"
              : "This role decides which laws apply next. For example, an heir triggers the Faraiz calculation and a deed buyer triggers the mutation check."}
          </p>
        </Step>

        <Step n={4} icon={Scale} title={L({ bn: "২৪টি আইনি যাচাই", en: "Running 24 legal checks" })}>
          <p>
            {bn
              ? "প্রতিটি যাচাই একটি নির্দিষ্ট আইনের ধারা থেকে এসেছে। গুরুত্ব অনুযায়ী তিন ভাগে ভাগ করা, আর প্রতিটির নির্দিষ্ট পয়েন্ট আছে। কোনো সমস্যা পাওয়া গেলে রিপোর্টে আইনের নাম, প্রমাণ, করণীয় এবং বিক্রেতাকে কী জিজ্ঞেস করবেন তা লেখা থাকে।"
              : "Each check comes from a specific section of law. They are grouped into three tiers by severity, and each has fixed points. When a problem is found, the report shows the law, the evidence, what to do and what to ask the seller."}
          </p>
          <RuleTable
            title={bn ? "গুরুতর (Critical)" : "Critical"}
            note={bn ? "যেকোনো একটি পাওয়া গেলেই ফলাফল উচ্চ ঝুঁকি" : "Any one of these makes the result HIGH"}
            rules={CRITICAL}
            tone="bg-high"
          />
          <RuleTable
            title={bn ? "বড় (Major)" : "Major"}
            note={bn ? "কেনার আগে অবশ্যই সমাধান করতে হবে" : "Must be resolved before buying"}
            rules={MAJOR}
            tone="bg-medium"
          />
          <RuleTable
            title={bn ? "ছোট (Minor)" : "Minor"}
            note={bn ? "সতর্ক থাকুন ও কাগজ দেখে নিন" : "Be careful and check the papers"}
            rules={MINOR}
            tone="bg-brand-500"
          />
        </Step>

        <Step n={5} icon={Calculator} title={L({ bn: "উত্তরাধিকার (ফারায়েজ) হিসাব", en: "Inheritance (Faraiz) calculation" })}>
          <p>
            {bn
              ? "বিক্রেতা যদি মৃত মালিকের ওয়ারিশ হন, তাহলে মুসলিম উত্তরাধিকার আইন (ফারায়েজ) অনুযায়ী প্রত্যেক ওয়ারিশের অংশ হিসাব করা হয়। স্ত্রী সন্তান থাকলে ১/৮ পান, না থাকলে ১/৪। ছেলে মেয়ের দ্বিগুণ পায়। বাবা ও মায়ের অংশ, আউল (অংশের যোগফল বেশি হলে আনুপাতিক কমানো) এবং রদ (বাকি অংশ ফেরত) নিয়মও হিসাবে আছে।"
              : "If the seller is an heir of a deceased owner, every heir's share is calculated under Muslim inheritance law (Faraiz). A wife gets 1/8 when there are children and 1/4 when there are none. A son gets twice a daughter's share. Shares of the father and mother, 'awl (proportional reduction when shares exceed the estate) and radd (return of the surplus) are also handled."}
          </p>
          <p className="font-semibold">
            {bn ? "উদাহরণ: আব্দুল মজিদ ২০২২ সালে মারা যান, জমি ১ একর।" : "Example: Abdul Majid died in 2022 leaving 1 acre."}
          </p>
          <div className="overflow-hidden rounded-xl border border-line bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-paper text-xs text-muted">
                <tr>
                  <th className="px-5 py-2 font-semibold">{bn ? "ওয়ারিশ" : "Heir"}</th>
                  <th className="px-5 py-2 font-semibold">{bn ? "সম্পর্ক" : "Relation"}</th>
                  <th className="px-5 py-2 font-semibold">{bn ? "অংশ" : "Share"}</th>
                  <th className="px-5 py-2 text-right font-semibold">{bn ? "একর" : "Acre"}</th>
                </tr>
              </thead>
              <tbody>
                {HEIRS.map((h) => (
                  <tr key={h.name.en} className="border-t border-line">
                    <td className="px-5 py-2.5 font-medium">{L(h.name)}</td>
                    <td className="px-5 py-2.5 text-muted">{L(h.relation)}</td>
                    <td className="px-5 py-2.5 font-mono">{num(h.share)}</td>
                    <td className="px-5 py-2.5 text-right font-mono">{num(h.acre)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>
            {bn
              ? "করিম মিয়া সর্বোচ্চ ০.৩৫ একর বিক্রি করতে পারেন। তিনি এর বেশি বিক্রি করতে চাইলে \"নিজের অংশের বেশি বিক্রি\" সমস্যা ধরা পড়ে। এটা ভূমি অপরাধ আইন ২০২৩ অনুযায়ী অপরাধ।"
              : "Karim Mia can sell at most 0.35 acre. If he tries to sell more, the check \"selling more than his share\" fires. This is an offence under the Land Crime Act 2023."}
          </p>
          <Link href="/inheritance" className="inline-flex font-semibold text-brand-700 hover:underline">
            {bn ? "ওয়ারিশ হিসাব নিজে করে দেখুন →" : "Try the inheritance calculator →"}
          </Link>
        </Step>

        <Step n={6} icon={BrainCircuit} title={L({ bn: "মেশিন লার্নিং দিয়ে প্রতারণার ধরন খোঁজা", en: "Finding fraud patterns with machine learning" })}>
          <p>
            {bn
              ? "নিয়মগুলো একটা একটা বিষয় আলাদা করে দেখে। কিন্তু চালাক প্রতারক প্রতিটা নিয়মের সীমার ঠিক নিচে থাকে। তাই আমরা Isolation Forest নামে একটি মেশিন লার্নিং মডেল ব্যবহার করেছি, যা প্রতিটি বিক্রির ৫টি তথ্য একসাথে দেখে:"
              : "Rules look at one thing at a time, but a clever fraudster stays just under every limit. So we use a machine learning model called Isolation Forest that looks at five facts of each sale together:"}
          </p>
          <NumberedList items={ML_FEATURES.map(L)} />
          <p>
            {bn
              ? "মডেলটি ২০,০০০টি কৃত্রিম বিক্রি দেখে শিখেছে স্বাভাবিক বিক্রি দেখতে কেমন। যে বিক্রি সেই ধরন থেকে অনেক আলাদা, তাকে খুব কম চেষ্টায় আলাদা করা যায়, আর মডেল তাকে অস্বাভাবিক বলে। আলাদা ৫,০০০টি কৃত্রিম বিক্রিতে পরীক্ষায় মডেল ৭১% প্রতারণা ধরেছে, আর স্বাভাবিক বিক্রিকে ভুল করে সন্দেহ করেছে মাত্র ১.৩%।"
              : "The model learned what a normal sale looks like from 20,000 synthetic sales. A sale that is very different can be isolated with very few splits, so the model marks it as unusual. On a separate test set of 5,000 synthetic sales it caught 71% of the fraud and wrongly flagged only 1.3% of normal sales."}
          </p>
          <p>
            {bn
              ? "মডেল একা কখনো জমিকে বিপজ্জনক বলে না। কোনো নিয়ম আগেই সমস্যা ধরলে মডেল শুধু বাড়তি প্রমাণ যোগ করে। কোনো নিয়ম না ধরলেও মডেল সন্দেহ করলে একটি \"বড়\" সতর্কতা (+২০) আসে, কারণসহ। ডেমো কেস ১৪ (সেলিম রেজা, দাগ ২৩৫) এর উদাহরণ: সব নিয়মে পরিষ্কার, কিন্তু মাত্র ১৪০ দিন আগে কিনে এক বছরে ৪টি দাগ বিক্রি করছেন।"
              : "The model never declares land unsafe on its own. If a rule already found the problem, the model only adds evidence. If no rule fired but the model is suspicious, a Major warning (+20) is shown with the reasons. Demo case 14 (Selim Reza, dag 235) shows this: clean under every rule, but he bought only 140 days ago and sold 4 dags in one year."}
          </p>
        </Step>

        <Step n={7} icon={Gauge} title={L({ bn: "ঝুঁকির স্কোর তৈরি", en: "Calculating the risk score" })}>
          <NumberedList
            items={[
              bn ? "পাওয়া সব সমস্যার পয়েন্ট যোগ করা হয়, সর্বোচ্চ ১০০।" : "The points of every finding are added, up to a maximum of 100.",
              bn ? "স্কোর ০ থেকে ৩০ হলে কম ঝুঁকি, ৩১ থেকে ৬০ হলে মাঝারি ঝুঁকি, ৬১ থেকে ১০০ হলে উচ্চ ঝুঁকি।" : "A score of 0 to 30 is LOW, 31 to 60 is MEDIUM, and 61 to 100 is HIGH.",
              bn ? "কোনো গুরুতর (Critical) সমস্যা থাকলে স্কোর যাই হোক, ফলাফল উচ্চ ঝুঁকি।" : "If any Critical finding exists, the result is HIGH regardless of the score.",
            ]}
          />
        </Step>

        <Step n={8} icon={QrCode} title={L({ bn: "সিল করা রিপোর্ট", en: "The sealed report" })}>
          <p>{bn ? "রিপোর্টে থাকে:" : "The report contains:"}</p>
          <NumberedList items={REPORT_PARTS.map(L)} />
          <p>
            {bn
              ? "রিপোর্ট তৈরির সময় পুরো ফলাফলের SHA-256 হ্যাশ বানিয়ে সংরক্ষণ করা হয় এবং একটি QR কোড দেওয়া হয়। কেউ রিপোর্টের একটা অক্ষরও বদলালে হ্যাশ মিলবে না। ব্যাংক, আইনজীবী বা পরিবারের যে কেউ QR স্ক্যান করে বা \"রিপোর্ট যাচাই\" পেজে গিয়ে দেখতে পারেন রিপোর্টটি আসল কিনা।"
              : "When the report is created, a SHA-256 hash of the full result is stored and a QR code is printed. If anyone changes even one character, the hash no longer matches. A bank, lawyer or family member can scan the QR code or use the \"Verify report\" page to confirm the report is genuine."}
          </p>
        </Step>

        <Step n={9} icon={MessageCircleQuestion} title={L({ bn: "রিপোর্ট নিয়ে প্রশ্ন করা", en: "Asking about the report" })}>
          <p>
            {bn
              ? "রিপোর্টের পাশে ক্রেতা সহজ বাংলায় প্রশ্ন করতে পারেন, যেমন \"হক-শুফা কী?\" বা \"আমি কি এই জমি কিনব?\"। Gemma 4 শুধু এই রিপোর্টের তথ্য ও সাধারণ ভূমি আইন থেকে উত্তর দেয়, কোনো নাম বা মামলা নম্বর বানায় না, এবং সবসময় মনে করিয়ে দেয় যে সরকারি যাচাই ও আইনজীবীর পরামর্শ দরকার। ঝুঁকির স্কোর সবসময় নিয়ম থেকে আসে; AI শুধু ব্যাখ্যা করে।"
              : "Next to the report, the buyer can ask in plain Bangla, for example \"What is Hak-e-Shufa?\" or \"Should I buy this land?\". Gemma 4 answers only from the report's facts and general land law, never invents names or case numbers, and always reminds the buyer that official verification and a lawyer are needed. The risk score always comes from the rules; the AI only explains it."}
          </p>
        </Step>

        <section className="border-t border-line py-10">
          <div className="flex items-center gap-3">
            <ShieldAlert className="size-6 text-medium" />
            <h2 className="text-2xl font-bold tracking-tight">{bn ? "সীমাবদ্ধতা" : "Limitations"}</h2>
          </div>
          <div className="mt-4 max-w-4xl">
            <NumberedList
              items={[
                bn ? "এটি সিদ্ধান্তে সহায়ক একটি টুল, সরকারি যাচাই বা আইনি পরামর্শের বিকল্প নয়।" : "This is decision support, not a replacement for official verification or legal advice.",
                bn ? "সব তথ্য কৃত্রিম। বাস্তবে চালু করতে ভূমি মন্ত্রণালয়ের রেকর্ডের সাথে অনুমোদিত সংযোগ লাগবে।" : "All data is synthetic. A real deployment needs an approved connection to Ministry of Land records.",
                bn ? "স্বয়ংক্রিয় উত্তরাধিকার হিসাব এখন শুধু মুসলিম আইনের জন্য; অন্য ক্ষেত্রে আইনজীবী দিয়ে যাচাইয়ের সতর্কতা দেওয়া হয়।" : "Automatic inheritance shares cover Muslim law only; for others the report asks for a lawyer's review.",
                bn ? "মেশিন লার্নিং মডেলের নির্ভুলতা কৃত্রিম ডেটায় মাপা; আসল ডেটা দিয়ে আবার প্রশিক্ষণ দিতে হবে।" : "The machine learning accuracy is measured on synthetic data; it must be retrained on real data.",
              ]}
            />
          </div>
        </section>
      </div>
    </div>
  );
}
