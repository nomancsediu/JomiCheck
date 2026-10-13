"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { LEVEL_COLOR } from "@/components/RiskGauge";
import { api, type Level, type MapPlot, type MouzaMap as MapData } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const LEVEL_TEXT: Record<Level, { bn: string; en: string }> = {
  LOW: { bn: "কম ঝুঁকি", en: "Low risk" },
  MEDIUM: { bn: "মাঝারি ঝুঁকি", en: "Medium risk" },
  HIGH: { bn: "উচ্চ ঝুঁকি", en: "High risk" },
};

function path(points: [number, number][]) {
  return points.map(([x, y], i) => `${i ? "L" : "M"}${x} ${y}`).join(" ") + " Z";
}

export function MouzaMap({ mouzaId, dagNo }: { mouzaId: number; dagNo: string }) {
  const { lang, num, pick } = useLang();
  const bn = lang === "bn";
  const [data, setData] = useState<MapData | null>(null);
  const [failed, setFailed] = useState(false);
  const [selected, setSelected] = useState<string>(dagNo);

  useEffect(() => {
    api.mouzaMap(mouzaId).then(setData).catch(() => setFailed(true));
  }, [mouzaId]);

  if (failed) return <p className="text-sm text-muted">{bn ? "নকশা লোড করা যায়নি।" : "Could not load the map."}</p>;
  if (!data) return <Loader2 className="size-5 animate-spin text-brand-700" />;

  const active: MapPlot | undefined = data.plots.find((p) => p.dag_no === selected);
  const neighbours = data.plots.filter((p) => p.dag_no !== dagNo);
  const risky = neighbours.filter((p) => p.level === "HIGH").length;

  return (
    <div>
      <p className="mb-3 text-sm text-muted">
        {bn
          ? `${pick(data.mouza.name)} মৌজার (জেএল ${num(data.mouza.jl_no)}) নকশা। আপনার দাগ মোটা দাগে চিহ্নিত; প্রতিটি দাগের রং দেখায় রেকর্ডধারী মালিক বিক্রি করলে ঝুঁকি কতটা। যেকোনো দাগে চাপ দিন।`
          : `Map sheet of ${pick(data.mouza.name)} mouza (JL ${data.mouza.jl_no}). Your dag has a thick outline; each colour shows the risk if the recorded owner sold that dag. Tap any dag.`}
      </p>

      <div className="overflow-x-auto rounded-lg border border-line bg-[#fbf8ef]">
        <svg viewBox={`0 0 ${data.width} ${data.height}`} className="block h-auto w-full min-w-[560px]" role="img"
          aria-label={bn ? "মৌজা নকশা" : "Mouza map"}>
          <defs>
            <pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="10" stroke="#1f2937" strokeWidth="2" strokeOpacity="0.35" />
            </pattern>
          </defs>
          {data.road && <path d={path(data.road)} fill="#e7e1d0" stroke="#a8a08a" strokeWidth="1.5" />}
          {data.road_label && (
            <text x={data.road_label[0]} y={data.road_label[1]} textAnchor="middle" dominantBaseline="middle" fontSize="17" fill="#6b6455">
              {bn ? "গ্রামের রাস্তা" : "Village road"}
            </text>
          )}
          {data.plots.map((p) => {
            const mine = p.dag_no === dagNo;
            const isSelected = p.dag_no === selected;
            return (
              <g key={p.id} onClick={() => setSelected(p.dag_no)} className="cursor-pointer">
                <path d={path(p.points)} fill={LEVEL_COLOR[p.level]} fillOpacity={mine ? 0.45 : isSelected ? 0.35 : 0.18}
                  stroke="#3f3a2f" strokeWidth="1.2" />
                {mine && <path d={path(p.points)} fill="url(#hatch)" stroke="#111827" strokeWidth="5" />}
                {isSelected && !mine && <path d={path(p.points)} fill="none" stroke="#111827" strokeWidth="2.5" strokeDasharray="8 5" />}
                <text x={p.label[0]} y={p.label[1]} textAnchor="middle" dominantBaseline="middle" fontSize={mine ? 26 : 20}
                  fontWeight={mine ? 700 : 600} fill="#1f2937" paintOrder="stroke" stroke="#fbf8ef" strokeWidth="4">
                  {num(p.dag_no)}
                </text>
              </g>
            );
          })}
          <g transform={`translate(${data.width - 40} 46)`} fill="#1f2937">
            <path d="M0 -24 L9 6 L0 0 L-9 6 Z" />
            <text y="24" textAnchor="middle" fontSize="14" fontWeight="700">{bn ? "উ" : "N"}</text>
          </g>
        </svg>
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        {(Object.keys(LEVEL_TEXT) as Level[]).map((l) => (
          <span key={l} className="inline-flex items-center gap-1.5">
            <span className="size-3 rounded-sm" style={{ background: LEVEL_COLOR[l], opacity: 0.6 }} /> {bn ? LEVEL_TEXT[l].bn : LEVEL_TEXT[l].en}
          </span>
        ))}
        <span>{bn ? "নকশাটি কৃত্রিম, জরিপ করা নয়।" : "Synthetic sheet, not surveyed."}</span>
        <span className="sm:hidden">{bn ? "পুরো নকশা দেখতে পাশে সরান।" : "Swipe sideways to see the whole sheet."}</span>
      </div>

      {active && (
        <div className="mt-4 rounded-lg border border-line px-4 py-3 text-sm">
          <p className="font-semibold">
            {bn ? "দাগ" : "Dag"} {num(active.dag_no)} · {num(active.area_acre)} {bn ? "একর" : "acre"}
            {active.dag_no === dagNo && <span className="ml-2 font-normal text-muted">({bn ? "আপনার দাগ" : "your dag"})</span>}
          </p>
          <p className="mt-1" style={{ color: LEVEL_COLOR[active.level] }}>
            {bn ? LEVEL_TEXT[active.level].bn : LEVEL_TEXT[active.level].en} ({num(active.score)}/{num(100)})
          </p>
          {active.flags.length > 0 && (
            <ul className="mt-1 list-disc pl-5 text-muted">
              {active.flags.map((f) => (
                <li key={f.en}>{pick(f)}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {risky > 0 && (
        <p className="mt-3 text-sm text-muted">
          {bn
            ? `পাশের ${num(risky)}টি দাগে উচ্চ ঝুঁকি আছে। সীমানা নিয়ে বিরোধ এড়াতে কেনার আগে আমিন দিয়ে মাপ করিয়ে নিন।`
            : `${risky} neighbouring dag(s) are high risk. Have an amin measure the boundary before you buy to avoid disputes.`}
        </p>
      )}
    </div>
  );
}
