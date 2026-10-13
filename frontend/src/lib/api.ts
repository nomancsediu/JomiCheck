export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export type Bi = { en: string; bn: string };
export type Level = "LOW" | "MEDIUM" | "HIGH";
export type Tier = "CRITICAL" | "MAJOR" | "MINOR";

export type Mouza = { id: number; name: Bi; jl_no: number };
export type Upazila = { id: number; name: Bi; mouzas: Mouza[] };
export type District = { id: number; name: Bi; upazilas: Upazila[] };

export type DemoCase = {
  key: string;
  title_en: string;
  title_bn: string;
  summary_en: string;
  summary_bn: string;
  mouza: string;
  mouza_bn: string;
  dag_no: string;
  khatian_no: string;
  seller_name: string;
  area_acre: string;
  district_id: number;
  upazila_id: number;
  mouza_id: number;
};

export type Flag = {
  code: string;
  tier: Tier;
  points: number;
  law: string;
  title: Bi;
  explanation: Bi;
  action: Bi;
  seller_question: Bi;
  evidence: string[];
};

export type TimelineEvent = {
  date: string;
  year_only: boolean;
  kind: "record" | "inheritance" | "deed" | "mutation" | "legal" | "mortgage" | "agreement" | "poa";
  status: "ok" | "warning" | "danger";
  title: Bi;
  detail: Bi;
};

export type LineageStep = {
  survey: string;
  khatian_no: string;
  record_year: number;
  owners: (Bi & { share: string })[];
  consistent: boolean;
};

export type HeirRow = {
  person_id?: number;
  name: Bi | string;
  relation: string;
  is_minor?: boolean;
  share: string;
  share_decimal: number;
  area_acre: string;
  basis: string;
};

export type Inheritance = {
  deceased: Bi;
  date_of_death: string | null;
  owner_share: string;
  estate_area_acre: string;
  heirs: HeirRow[];
  notes: string[];
  law: string;
};

export type KhatianOwnerRow = {
  serial?: number;
  name: Bi;
  father?: Bi | null;
  share: string;
  share_ana?: Bi & { exact: boolean };
  area_acre: string;
  is_deceased: boolean;
  is_minor: boolean;
  is_government: boolean;
  death_year?: number | null;
};

export type RecordOfRights = {
  survey: string;
  khatian_no: string;
  record_year: number;
  mutation_case_no?: string | null;
  dag_no?: string;
  land_class?: Bi;
  plot_area_acre?: string;
  owners: KhatianOwnerRow[];
};

export type VerificationResult = {
  plot: {
    id: number;
    dag_no: string;
    area_acre: string;
    land_class: string;
    land_class_bn: string;
    mouza_rate_per_acre: number;
    mouza: Bi & { jl_no: number };
    upazila: Bi;
    district: Bi;
  };
  input: { seller_name: string; area_acre: string; khatian_no: string };
  seller: {
    matched: boolean;
    match_score: number;
    name: Bi;
    role: "owner" | "heir" | "deed_buyer" | "attorney" | "deceased_owner" | "none";
    sellable_area_acre: string | null;
    prior_sold_acre: string;
  };
  record_of_rights: RecordOfRights | null;
  flags: Flag[];
  score: number;
  level: Level;
  inheritance: Inheritance | null;
  lineage: LineageStep[];
  timeline: TimelineEvent[];
  notes: Bi[];
  summary: Bi;
  documents: Bi[];
  next_steps: Bi[];
  seller_questions: Bi[];
  site_visit: Bi[];
};

export type Report = {
  id: string;
  created_at: string;
  sha256: string;
  verify_url: string;
  qr_svg: string;
  result: VerificationResult;
};

export type ReportCheck = {
  authentic: boolean;
  reason: "match" | "hash_mismatch" | "registry_record_modified" | "not_found";
  id?: string;
  created_at?: string;
  sha256?: string;
  facts?: {
    plot: VerificationResult["plot"];
    seller: Bi;
    area_acre: string;
    score: number;
    level: Level;
    flags: Bi[];
  };
};

export type AreaType = "city_major" | "city_other" | "pourashava" | "union";

export type CostLine = { key: string; label: Bi; rate_percent: string | null; amount: number };

export type CostEstimate = {
  price_bdt: number;
  area_type: AreaType;
  area_type_label: Bi;
  mouza_minimum_bdt: number | null;
  below_minimum: boolean;
  deed_value_bdt: number;
  registration: CostLine[];
  registration_total: number;
  mutation: CostLine[];
  mutation_total: number;
  fees_total: number;
  grand_total: number;
  rates_as_of: string;
  notes: Bi[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body: unknown,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = (body as { detail?: string } | null)?.detail ?? `Request failed (${res.status})`;
    throw new ApiError(detail, res.status, body);
  }
  return body as T;
}

export const api = {
  locations: () => request<District[]>("/locations/"),
  plots: (mouzaId: number) => request<{ dag_no: string; area_acre: string }[]>(`/mouzas/${mouzaId}/plots/`),
  demoCases: () => request<DemoCase[]>("/demo-cases/"),
  verify: (payload: {
    mouza_id: number;
    dag_no: string;
    seller_name: string;
    area_acre: string;
    khatian_no?: string;
    buyer_token?: string;
  }) => request<Report>("/verify/", { method: "POST", body: JSON.stringify(payload) }),
  report: (id: string) => request<Report>(`/reports/${id}/`),
  checkReport: (id: string, hash: string) =>
    request<ReportCheck>(`/reports/${id}/verify/?h=${encodeURIComponent(hash)}`),
  ask: (id: string, question: string, lang: "bn" | "en") =>
    request<{ answer: string; source: "llm" | "built-in" }>(`/reports/${id}/ask/`, {
      method: "POST",
      body: JSON.stringify({ question, lang }),
    }),
  costEstimate: (payload: { price_bdt: number; area_type: AreaType; area_acre?: string; mouza_rate_per_acre?: number }) =>
    request<CostEstimate>("/costs/estimate/", { method: "POST", body: JSON.stringify(payload) }),
  inheritance: (payload: { area_acre: string; heirs: { relation: string; name?: string }[] }) =>
    request<{ area_acre: string; heirs: HeirRow[]; notes: string[]; law: string }>("/inheritance/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export function buyerToken(): string {
  if (typeof window === "undefined") return "";
  const key = "jomicheck_buyer_token";
  let token = window.localStorage.getItem(key);
  if (!token) {
    token = crypto.randomUUID();
    window.localStorage.setItem(key, token);
  }
  return token;
}
