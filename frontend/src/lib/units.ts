import type { Bi } from "./api";

export type AreaUnit = { key: string; label: Bi; acre: number };

const SQFT_PER_ACRE = 43560;

export const AREA_UNITS: AreaUnit[] = [
  { key: "decimal", label: { bn: "শতাংশ (শতক)", en: "Decimal (shotok)" }, acre: 0.01 },
  { key: "katha", label: { bn: "কাঠা", en: "Katha" }, acre: 720 / SQFT_PER_ACRE },
  { key: "bigha", label: { bn: "বিঘা", en: "Bigha" }, acre: 14400 / SQFT_PER_ACRE },
  { key: "acre", label: { bn: "একর", en: "Acre" }, acre: 1 },
  { key: "ojutangsho", label: { bn: "অযুতাংশ", en: "Ojutangsho" }, acre: 0.0001 },
  { key: "sqft", label: { bn: "বর্গফুট", en: "Square feet" }, acre: 1 / SQFT_PER_ACRE },
  { key: "sqm", label: { bn: "বর্গমিটার", en: "Square metre" }, acre: 1 / 4046.8564224 },
  { key: "hectare", label: { bn: "হেক্টর", en: "Hectare" }, acre: 2.4710538147 },
];

export function toAcre(value: number, unitKey: string): number {
  const unit = AREA_UNITS.find((u) => u.key === unitKey);
  return unit ? value * unit.acre : value;
}

export function fromAcre(acre: number, unitKey: string): number {
  const unit = AREA_UNITS.find((u) => u.key === unitKey);
  return unit ? acre / unit.acre : acre;
}

export function formatArea(value: number): string {
  if (!Number.isFinite(value)) return "—";
  if (value >= 1000) return Math.round(value).toLocaleString("en-IN");
  return String(Number(value.toPrecision(5)));
}

export function formatTaka(value: number): string {
  return Math.round(value).toLocaleString("en-IN");
}
