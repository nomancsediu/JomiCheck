"use client";

import type { RecordOfRights, VerificationResult } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const th = "border border-line bg-paper px-2.5 py-2 text-left align-bottom text-xs font-semibold text-ink/80";
const td = "border border-line px-2.5 py-2 align-top";

function ColNo({ n }: { n: number }) {
  const { num } = useLang();
  return <span className="block font-mono text-[10px] font-normal text-muted">({num(n)})</span>;
}

export function KhatianSheet({ ror, plot }: { ror: RecordOfRights; plot: VerificationResult["plot"] }) {
  const { t, pick, num, lang } = useLang();
  const surveyLabel = ror.survey === "NAMJARI" ? t("ks_survey_NAMJARI") : `${ror.survey} ${lang === "bn" ? "খতিয়ান" : "khatian"}`;
  const landClass = ror.land_class ?? { en: plot.land_class, bn: plot.land_class_bn ?? plot.land_class };
  const plotArea = ror.plot_area_acre ?? plot.area_acre;
  const khatianShare = ror.owners.reduce((sum, o) => sum + Number(o.share), 0);
  const khatianArea = ror.owners.reduce((sum, o) => sum + Number(o.area_acre), 0);
  const fmt = (v: number) => num(String(Number(v.toFixed(4))));

  const meta: [string, string][] = [
    [t("district"), pick(plot.district)],
    [t("upazila"), pick(plot.upazila)],
    [t("mouza"), `${pick(plot.mouza)} · JL ${num(plot.mouza.jl_no)}`],
    [t("ks_khatian"), num(ror.khatian_no)],
    [t("ks_record_year"), num(ror.record_year)],
  ];
  if (ror.mutation_case_no) meta.push([t("ks_mutation_case"), num(ror.mutation_case_no)]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b-2 border-ink pb-2">
        <p className="text-base font-bold tracking-tight">{surveyLabel}</p>
        <p className="font-mono text-xs text-muted">{t("ks_khatian")} {num(ror.khatian_no)}</p>
      </div>

      <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:grid-cols-3">
        {meta.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-2 border-b border-dashed border-line py-1">
            <dt className="text-muted">{k}</dt>
            <dd className="text-right font-medium">{v}</dd>
          </div>
        ))}
      </dl>

      <div>
        <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">{t("ks_owner_part")}</p>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className={`${th} w-16`}><ColNo n={1} />{t("ks_serial")}</th>
                <th className={th}><ColNo n={2} />{t("ks_owner_name")}</th>
                <th className={th}><ColNo n={3} />{t("ks_share")}</th>
                <th className={th}><ColNo n={4} />{t("ks_remarks")}</th>
              </tr>
            </thead>
            <tbody>
              {ror.owners.map((o, i) => {
                const remarks: string[] = [];
                if (o.is_government) remarks.push(t("ks_government"));
                if (o.is_deceased) remarks.push(o.death_year ? `${t("deceased")} (${t("ks_died")} ${num(o.death_year)})` : t("deceased"));
                if (o.is_minor) remarks.push(t("minor"));
                return (
                  <tr key={o.name.en}>
                    <td className={`${td} font-mono`}>{num(o.serial ?? i + 1)}</td>
                    <td className={td}>
                      <span className="font-medium">{pick(o.name)}</span>
                      {o.father && (
                        <span className="block text-xs text-muted">
                          {t("ks_father")}: {pick(o.father)}
                        </span>
                      )}
                    </td>
                    <td className={td}>
                      <span className="font-medium">{o.share_ana ? pick(o.share_ana) : num(o.share)}</span>
                      <span className="block font-mono text-xs text-muted">{num(o.share)}</span>
                    </td>
                    <td className={`${td} ${remarks.length ? "text-medium" : "text-muted"}`}>{remarks.join(", ") || "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">{t("ks_plot_part")}</p>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className={th}><ColNo n={5} />{t("ks_dag")}</th>
                <th className={th}><ColNo n={6} />{t("ks_class")}</th>
                <th className={th}><ColNo n={7} />{t("ks_dag_area")}</th>
                <th className={th}><ColNo n={8} />{t("ks_share")}</th>
                <th className={th}><ColNo n={9} />{t("ks_khatian_area")}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className={`${td} font-mono font-medium`}>{num(ror.dag_no ?? plot.dag_no)}</td>
                <td className={td}>{pick(landClass)}</td>
                <td className={`${td} font-mono`}>{num(plotArea)} {t("acre")}</td>
                <td className={`${td} font-mono`}>{fmt(khatianShare)}</td>
                <td className={`${td} font-mono`}>{fmt(khatianArea)} {t("acre")}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
