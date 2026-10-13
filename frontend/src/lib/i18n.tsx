"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useSyncExternalStore } from "react";
import type { Bi } from "./api";

export type Lang = "bn" | "en";

const BN_DIGITS = "০১২৩৪৫৬৭৮৯";

export function toBnDigits(value: string | number): string {
  return String(value).replace(/[0-9]/g, (d) => BN_DIGITS[Number(d)]);
}

const dict = {
  brand_tagline: { bn: "কেনার আগে যাচাই করুন", en: "Check before you buy" },
  nav_verify: { bn: "জমি যাচাই", en: "Verify land" },
  nav_inheritance: { bn: "ওয়ারিশ হিসাব", en: "Inheritance" },
  nav_check_report: { bn: "রিপোর্ট যাচাই", en: "Check a report" },
  nav_forgery: { bn: "জাল কাগজ", en: "Forged papers" },
  nav_how: { bn: "কীভাবে কাজ করে", en: "How it works" },
  hiw_title: { bn: "JomiCheck কীভাবে কাজ করে", en: "How JomiCheck works" },
  hiw_step: { bn: "ধাপ", en: "Step" },
  nav_costs: { bn: "খরচ ও একক", en: "Costs & units" },
  nav_upload: { bn: "ডকুমেন্ট আপলোড", en: "Upload document" },
  upload_cta: { bn: "খতিয়ানের ছবি থেকে পূরণ করুন", en: "Fill from a khatian photo" },
  start_verification: { bn: "যাচাই শুরু করুন", en: "Start verification" },

  hero_title: { bn: "জমি কেনার আগে, একজন অভিজ্ঞ আইনজীবীর মতো যাচাই করুন", en: "Before you buy land, check it the way an experienced lawyer would" },
  hero_body: {
    bn: "দাগ, খতিয়ান ও বিক্রেতার নাম দিন। জমিচেক মালিকানা, ওয়ারিশ অংশ, নামজারি, মামলা, খাস ও অধিগ্রহণ, বন্ধক এবং একাধিকবার বিক্রি যাচাই করে প্রতিটি ঝুঁকি আইনের ধারাসহ সহজ ভাষায় ব্যাখ্যা করে।",
    en: "Enter the Dag, Khatian and seller's name. JomiCheck checks ownership, inheritance shares, mutation, litigation, khas and acquisition status, mortgages and double-selling, and explains every risk in plain language with the relevant law.",
  },
  stat_checks: { bn: "আইনি যাচাই", en: "legal checks" },
  stat_surveys: { bn: "জরিপ প্রজন্ম", en: "survey generations" },
  stat_minutes: { bn: "মিনিটে রিপোর্ট", en: "minute report" },

  section_checks: { bn: "যা যা যাচাই করা হয়", en: "What JomiCheck checks" },
  section_checks_sub: { bn: "একজন ভূমি আইনজীবী ক্রয়ের আগে যে বিষয়গুলো দেখেন, সবগুলো এক জায়গায়।", en: "Everything a land lawyer reviews before a purchase, in one place." },
  section_how: { bn: "কীভাবে কাজ করে", en: "How it works" },
  section_tools: { bn: "নিয়মের বাইরেও যা করে", en: "Beyond rule checks" },
  section_tools_sub: { bn: "কৃত্রিম বুদ্ধিমত্তা, মেশিন লার্নিং ও ডিজিটাল সিল — যাতে যাচাই দ্রুত, গভীর ও বিশ্বাসযোগ্য হয়।", en: "AI, machine learning and a digital seal make each check faster, deeper and trustworthy." },

  form_title: { bn: "জমির তথ্য দিন", en: "Enter land details" },
  form_sub: { bn: "খতিয়ান বা দলিলে যেভাবে লেখা আছে সেভাবে দিন।", en: "Enter the details as written on the khatian or deed." },
  district: { bn: "জেলা", en: "District" },
  upazila: { bn: "উপজেলা", en: "Upazila" },
  mouza: { bn: "মৌজা", en: "Mouza" },
  dag_no: { bn: "দাগ নম্বর", en: "Dag number" },
  khatian_no: { bn: "খতিয়ান নম্বর", en: "Khatian number" },
  optional: { bn: "ঐচ্ছিক", en: "optional" },
  seller_name: { bn: "বিক্রেতার নাম", en: "Seller's name" },
  seller_hint: { bn: "বাংলা বা ইংরেজিতে লিখতে পারেন", en: "Bangla or English" },
  area: { bn: "জমির পরিমাণ (একর)", en: "Area to buy (acre)" },
  select: { bn: "নির্বাচন করুন", en: "Select" },
  run_check: { bn: "যাচাই করুন", en: "Run verification" },
  checking: { bn: "যাচাই চলছে…", en: "Checking…" },
  quick_fill: { bn: "দ্রুত পূরণ: ডেমো কেস", en: "Quick fill: demo cases" },
  decimal: { bn: "শতাংশ", en: "decimal" },

  risk_level: { bn: "ঝুঁকির মাত্রা", en: "Risk level" },
  level_LOW: { bn: "কম ঝুঁকি", en: "Low risk" },
  level_MEDIUM: { bn: "মাঝারি ঝুঁকি", en: "Medium risk" },
  level_HIGH: { bn: "উচ্চ ঝুঁকি", en: "High risk" },
  tier_CRITICAL: { bn: "গুরুতর", en: "Critical" },
  tier_MAJOR: { bn: "বড়", en: "Major" },
  tier_MINOR: { bn: "ছোট", en: "Minor" },
  findings: { bn: "যা পাওয়া গেছে", en: "Findings" },
  document_check: { bn: "আপলোড করা কাগজ বনাম সরকারি রেকর্ড", en: "Uploaded papers versus official record" },
  no_findings: { bn: "কোনো ঝুঁকি পাওয়া যায়নি।", en: "No risk found." },
  law: { bn: "আইন", en: "Law" },
  what_to_do: { bn: "করণীয়", en: "What to do" },
  evidence: { bn: "প্রমাণ", en: "Evidence" },
  seller: { bn: "বিক্রেতা", en: "Seller" },
  role: { bn: "ভূমিকা", en: "Role" },
  role_owner: { bn: "রেকর্ডভুক্ত মালিক", en: "Recorded owner" },
  role_heir: { bn: "মৃত মালিকের ওয়ারিশ", en: "Heir of deceased owner" },
  role_deed_buyer: { bn: "দলিলে ক্রেতা (নামজারি হয়নি)", en: "Deed buyer (not mutated)" },
  role_attorney: { bn: "আমমোক্তার", en: "Power-of-attorney holder" },
  role_deceased_owner: { bn: "মৃত মালিকের নামে", en: "In a deceased owner's name" },
  role_none: { bn: "কোনো অধিকার পাওয়া যায়নি", en: "No recorded right" },
  can_sell: { bn: "বিক্রি করতে পারেন", en: "Can sell" },
  selling: { bn: "বিক্রি করছেন", en: "Selling" },
  acre: { bn: "একর", en: "acre" },
  record_of_rights: { bn: "সর্বশেষ খতিয়ান", en: "Latest record of rights" },
  owner: { bn: "মালিক", en: "Owner" },
  ks_owner_part: { bn: "মালিকানা অংশ", en: "Ownership part" },
  ks_plot_part: { bn: "দাগের বিবরণ", en: "Plot part" },
  ks_serial: { bn: "ক্রমিক নং", en: "Serial" },
  ks_owner_name: { bn: "মালিকের নাম ও পিতার নাম", en: "Owner and father's name" },
  ks_share: { bn: "অংশ বা হিস্যা", en: "Share (hissa)" },
  ks_dag: { bn: "দাগ নম্বর", en: "Dag no." },
  ks_class: { bn: "জমির শ্রেণি", en: "Land class" },
  ks_dag_area: { bn: "দাগে মোট জমি", en: "Total in dag" },
  ks_khatian_area: { bn: "খতিয়ানভুক্ত জমি", en: "Area in this khatian" },
  ks_remarks: { bn: "মন্তব্য", en: "Remarks" },
  ks_father: { bn: "পিতা", en: "father" },
  ks_government: { bn: "সরকার (খাস খতিয়ান)", en: "Government (khas khatian)" },
  ks_mutation_case: { bn: "নামজারি কেস", en: "Mutation case" },
  ks_record_year: { bn: "রেকর্ড বছর", en: "Record year" },
  ks_khatian: { bn: "খতিয়ান নং", en: "Khatian no." },
  ks_survey_NAMJARI: { bn: "নামজারি খতিয়ান", en: "Mutation khatian" },
  ks_died: { bn: "মৃত্যু", en: "died" },
  share: { bn: "অংশ", en: "Share" },
  deceased: { bn: "মৃত", en: "Deceased" },
  minor: { bn: "নাবালক", en: "Minor" },
  timeline: { bn: "মালিকানার ইতিহাস", en: "Ownership history" },
  lineage: { bn: "জরিপ ধারাবাহিকতা", en: "Survey lineage" },
  lineage_break: { bn: "ধারাবাহিকতা নেই", en: "Unexplained change" },
  inheritance: { bn: "ওয়ারিশ অংশ (ফারায়েজ)", en: "Inheritance shares (Faraiz)" },
  heir: { bn: "ওয়ারিশ", en: "Heir" },
  relation: { bn: "সম্পর্ক", en: "Relation" },
  documents: { bn: "যে কাগজ সংগ্রহ করবেন", en: "Documents to collect" },
  next_steps: { bn: "পরবর্তী পদক্ষেপ", en: "Next steps" },
  seller_questions: { bn: "বিক্রেতাকে যা জিজ্ঞেস করবেন", en: "Questions for the seller" },
  site_visit: { bn: "সরেজমিন পরিদর্শন", en: "Site visit checklist" },
  ask_title: { bn: "রিপোর্ট নিয়ে প্রশ্ন করুন", en: "Ask about this report" },
  ask_placeholder: { bn: "যেমন: হক-শুফা কী? আমি কি কিনব?", en: "e.g. What is pre-emption? Should I buy?" },
  ask_send: { bn: "জিজ্ঞেস করুন", en: "Ask" },
  ask_source_builtin: { bn: "অফলাইন শব্দকোষ", en: "Built-in glossary" },
  integrity: { bn: "রিপোর্টের সত্যতা", en: "Report integrity" },
  integrity_body: { bn: "QR কোড স্ক্যান করে যে কেউ যাচাই করতে পারবেন রিপোর্টটি পরিবর্তন করা হয়েছে কিনা।", en: "Anyone can scan the QR code to confirm this report has not been altered." },
  report_id: { bn: "রিপোর্ট আইডি", en: "Report ID" },
  generated: { bn: "তৈরি", en: "Generated" },
  print: { bn: "প্রিন্ট / PDF", en: "Print / PDF" },
  new_check: { bn: "নতুন যাচাই", en: "New check" },
  estimate_cost: { bn: "খরচ হিসাব", en: "Estimate cost" },
  disclaimer: {
    bn: "জমিচেক সিদ্ধান্ত গ্রহণে সহায়ক একটি ঝুঁকি-যাচাই টুল; এটি সরকারি যাচাই বা আইনি পরামর্শের বিকল্প নয়। এই প্রোটোটাইপের সকল তথ্য কৃত্রিম (সিনথেটিক)।",
    en: "JomiCheck is a decision-support and risk-screening tool, not official verification or legal advice. All data in this prototype is synthetic.",
  },
  plot: { bn: "দাগ", en: "Dag" },
  land_class: { bn: "জমির শ্রেণি", en: "Land class" },
  total_area: { bn: "মোট জমি", en: "Total area" },
  notes: { bn: "লক্ষ্য করুন", en: "Note" },
  loading: { bn: "লোড হচ্ছে…", en: "Loading…" },
  error_generic: { bn: "কিছু একটা সমস্যা হয়েছে। আবার চেষ্টা করুন।", en: "Something went wrong. Please try again." },
  backend_down: { bn: "সার্ভারের সাথে সংযোগ হচ্ছে না। ব্যাকএন্ড চালু আছে কিনা দেখুন।", en: "Cannot reach the server. Make sure the backend is running." },
} as const satisfies Record<string, Bi>;

export type DictKey = keyof typeof dict;

type Ctx = {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: DictKey) => string;
  pick: (bi: Bi | null | undefined) => string;
  num: (value: string | number) => string;
};

const LangContext = createContext<Ctx | null>(null);

const LANG_KEY = "jomicheck_lang";
const langListeners = new Set<() => void>();

function subscribeLang(cb: () => void) {
  langListeners.add(cb);
  window.addEventListener("storage", cb);
  return () => {
    langListeners.delete(cb);
    window.removeEventListener("storage", cb);
  };
}

const readLang = (): Lang => (window.localStorage.getItem(LANG_KEY) === "en" ? "en" : "bn");
const serverLang = (): Lang => "bn";

export function LangProvider({ children }: { children: React.ReactNode }) {
  const lang = useSyncExternalStore(subscribeLang, readLang, serverLang);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((l: Lang) => {
    window.localStorage.setItem(LANG_KEY, l);
    langListeners.forEach((cb) => cb());
  }, []);

  const value = useMemo<Ctx>(
    () => ({
      lang,
      setLang,
      t: (key) => dict[key][lang],
      pick: (bi) => (bi ? bi[lang] : ""),
      num: (value) => (lang === "bn" ? toBnDigits(value) : String(value)),
    }),
    [lang, setLang],
  );

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang(): Ctx {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error("useLang must be used inside LangProvider");
  return ctx;
}
