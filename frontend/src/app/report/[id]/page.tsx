"use client";

import { CheckSquare, ClipboardList, Info, MapPin, MessageSquareText, Plus, Printer, Square, Footprints } from "lucide-react";
import Link from "next/link";
import { use, useEffect, useState } from "react";
import { AskPanel } from "@/components/report/AskPanel";
import { FlagCard } from "@/components/report/FlagCard";
import { InheritanceTable } from "@/components/report/InheritanceTable";
import { IntegrityCard } from "@/components/report/IntegrityCard";
import { KhatianSheet } from "@/components/report/KhatianSheet";
import { Lineage } from "@/components/report/Lineage";
import { Timeline } from "@/components/report/Timeline";
import { LEVEL_COLOR, LevelBadge, RiskGauge } from "@/components/RiskGauge";
import { api, type Bi, type Report, type VerificationResult } from "@/lib/api";
import { useLang, type DictKey } from "@/lib/i18n";

function Card({ title, icon, children, className = "" }: { title: string; icon?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <section className={`print-avoid rounded-xl border border-line bg-white ${className}`}>
      <header className="flex items-center gap-2 border-b border-line px-5 py-3">
        {icon}
        <h2 className="font-semibold">{title}</h2>
      </header>
      <div className="p-5">{children}</div>
    </section>
  );
}

function Checklist({ items }: { items: Bi[] }) {
  const { pick } = useLang();
  const [done, setDone] = useState<Set<number>>(new Set());
  return (
    <ul className="space-y-2">
      {items.map((item, i) => {
        const checked = done.has(i);
        return (
          <li key={i}>
            <button
              onClick={() =>
                setDone((d) => {
                  const n = new Set(d);
                  if (n.has(i)) n.delete(i);
                  else n.add(i);
                  return n;
                })
              }
              className="flex w-full items-start gap-2.5 text-left text-sm"
            >
              {checked ? (
                <CheckSquare className="mt-0.5 size-4 shrink-0 text-brand-600" />
              ) : (
                <Square className="mt-0.5 size-4 shrink-0 text-muted" />
              )}
              <span className={checked ? "text-muted line-through" : "text-ink"}>{pick(item)}</span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function SellerCard({ r }: { r: VerificationResult }) {
  const { t, pick, num } = useLang();
  const sellable = r.seller.sellable_area_acre === null ? null : Number(r.seller.sellable_area_acre);
  const selling = Number(r.input.area_acre);
  const total = Number(r.plot.area_acre);
  const scale = Math.max(total, selling, sellable ?? 0);
  const over = sellable !== null && selling > sellable + 0.0001;

  return (
    <section className="rounded-xl border border-line bg-white p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{t("seller")}</p>
      <p className="mt-1 text-xl font-semibold">{pick(r.seller.name)}</p>
      <p className={`mt-1 text-sm font-medium ${r.seller.role === "owner" ? "text-low" : r.seller.role === "none" ? "text-high" : "text-medium"}`}>
        {t(`role_${r.seller.role}` as DictKey)}
      </p>
      <div className="mt-5 space-y-3 text-sm">
        <div>
          <div className="flex justify-between">
            <span className="text-muted">{t("can_sell")}</span>
            <span className="font-mono font-medium">{sellable === null ? "—" : `${num(sellable)} ${t("acre")}`}</span>
          </div>
          <div className="mt-1 h-2.5 rounded-full bg-paper">
            <div className="h-2.5 rounded-full bg-brand-600" style={{ width: `${((sellable ?? 0) / scale) * 100}%` }} />
          </div>
        </div>
        <div>
          <div className="flex justify-between">
            <span className="text-muted">{t("selling")}</span>
            <span className={`font-mono font-medium ${over ? "text-high" : ""}`}>
              {num(r.input.area_acre)} {t("acre")}
            </span>
          </div>
          <div className="mt-1 h-2.5 rounded-full bg-paper">
            <div className={`h-2.5 rounded-full ${over ? "bg-high" : "bg-brand-200"}`} style={{ width: `${(selling / scale) * 100}%` }} />
          </div>
        </div>
      </div>
    </section>
  );
}

function PlotCard({ r }: { r: VerificationResult }) {
  const { t, pick, num } = useLang();
  const rows: [string, string][] = [
    [t("district"), pick(r.plot.district)],
    [t("upazila"), pick(r.plot.upazila)],
    [t("mouza"), `${pick(r.plot.mouza)} (JL ${num(r.plot.mouza.jl_no)})`],
    [t("total_area"), `${num(r.plot.area_acre)} ${t("acre")}`],
    [t("land_class"), pick({ en: r.plot.land_class, bn: r.plot.land_class_bn ?? r.plot.land_class })],
  ];
  return (
    <section className="rounded-xl border border-line bg-white p-5">
      <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
        <MapPin className="size-3.5" /> {t("plot")} {num(r.plot.dag_no)}
      </p>
      <dl className="mt-3 space-y-1.5 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-4">
            <dt className="text-muted">{k}</dt>
            <dd className="text-right font-medium">{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t, pick, num, lang } = useLang();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.report(id).then(setReport).catch(() => setError(true));
  }, [id]);

  if (error) {
    return <p className="mx-auto max-w-3xl px-4 py-20 text-center text-muted">{t("error_generic")}</p>;
  }
  if (!report) {
    return <p className="mx-auto max-w-3xl px-4 py-20 text-center text-muted">{t("loading")}</p>;
  }

  const r = report.result;
  const created = new Date(report.created_at);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-xs text-muted">
            {t("report_id")} {report.id} · {t("generated")} {num(created.toLocaleString("en-GB"))}
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">
            {t("plot")} {num(r.plot.dag_no)}, {pick(r.plot.mouza)}, {pick(r.plot.upazila)}
          </h1>
        </div>
        <div className="no-print flex gap-2">
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-md border border-line bg-white px-4 py-2 text-sm font-medium hover:border-brand-500"
          >
            <Printer className="size-4" /> {t("print")}
          </button>
          <Link
            href="/verify"
            className="inline-flex items-center gap-2 rounded-md bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800"
          >
            <Plus className="size-4" /> {t("new_check")}
          </Link>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.35fr_1fr_1fr]">
        <section
          className="flex flex-col items-center gap-4 rounded-xl border-2 bg-white p-5 sm:flex-row sm:items-center"
          style={{ borderColor: LEVEL_COLOR[r.level] }}
        >
          <RiskGauge score={r.score} level={r.level} size={200} />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">{t("risk_level")}</p>
            <div className="mt-2">
              <LevelBadge level={r.level} large />
            </div>
            <p className="mt-3 text-sm leading-relaxed text-ink/90">{pick(r.summary)}</p>
          </div>
        </section>
        <SellerCard r={r} />
        <PlotCard r={r} />
      </div>

      {r.notes.length > 0 && (
        <div className="mt-4 space-y-2">
          {r.notes.map((n) => (
            <p key={n.en} className="flex items-center gap-2 rounded-lg border border-brand-200 bg-brand-50 px-4 py-2.5 text-sm text-brand-900">
              <Info className="size-4 shrink-0" /> {pick(n)}
            </p>
          ))}
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_380px]">
        <div className="space-y-6">
          <section>
            <h2 className="mb-3 text-lg font-semibold">
              {t("findings")} <span className="font-normal text-muted">({num(r.flags.length)})</span>
            </h2>
            {r.flags.length === 0 ? (
              <p className="rounded-lg border border-line bg-white p-5 text-sm text-low">{t("no_findings")}</p>
            ) : (
              <div className="space-y-3">
                {r.flags.map((f) => (
                  <FlagCard key={f.code} flag={f} />
                ))}
              </div>
            )}
          </section>

          {r.record_of_rights && (
            <Card title={t("record_of_rights")}>
              <KhatianSheet ror={r.record_of_rights} plot={r.plot} />
            </Card>
          )}

          {r.inheritance && (
            <Card title={t("inheritance")}>
              <p className="mb-3 text-sm text-muted">
                {pick(r.inheritance.deceased)} ({t("deceased")}
                {r.inheritance.date_of_death ? ` ${num(r.inheritance.date_of_death.slice(0, 4))}` : ""}) · {t("total_area")}{" "}
                {num(r.inheritance.estate_area_acre)} {t("acre")} · {r.inheritance.law}
              </p>
              <InheritanceTable heirs={r.inheritance.heirs} highlightId={r.inheritance.heirs.find((h) => typeof h.name !== "string" && h.name.en === r.seller.name.en)?.person_id} />
              {r.inheritance.notes.map((n) => (
                <p key={n} className="mt-2 text-xs text-muted">
                  {n}
                </p>
              ))}
            </Card>
          )}

          <Card title={t("lineage")}>
            <Lineage steps={r.lineage} />
          </Card>

          <Card title={t("timeline")}>
            <Timeline events={r.timeline} />
          </Card>
        </div>

        <aside className="space-y-6 lg:sticky lg:top-24 lg:self-start">
          <AskPanel reportId={report.id} />
          <IntegrityCard report={report} />
        </aside>
      </div>

      <div className="print-break mt-8 grid gap-6 md:grid-cols-2">
        <Card title={t("documents")} icon={<ClipboardList className="size-5 text-brand-700" />}>
          <Checklist items={r.documents} />
        </Card>
        <Card title={t("next_steps")} icon={<Footprints className="size-5 text-brand-700" />}>
          <ol className="list-decimal space-y-2 pl-5 text-sm marker:text-muted">
            {r.next_steps.map((s, i) => (
              <li key={i}>{pick(s)}</li>
            ))}
          </ol>
        </Card>
        <Card title={t("seller_questions")} icon={<MessageSquareText className="size-5 text-brand-700" />}>
          <ul className="space-y-2 text-sm">
            {r.seller_questions.map((q, i) => (
              <li key={i} className="rounded-md bg-paper px-3 py-2">
                “{pick(q)}”
              </li>
            ))}
          </ul>
        </Card>
        <Card title={t("site_visit")} icon={<MapPin className="size-5 text-brand-700" />}>
          <Checklist items={r.site_visit} />
        </Card>
      </div>

      <p className="mt-8 border-t border-line pt-4 text-xs text-muted">{t("disclaimer")}</p>
      <p className="hidden text-xs text-muted print:block">{lang === "bn" ? "জমিচেক" : "JomiCheck"} · {report.verify_url}</p>
    </div>
  );
}
