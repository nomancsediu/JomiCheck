"use client";

import { Loader2 } from "lucide-react";
import { useLang } from "@/lib/i18n";

export function PageLoading() {
  const { t } = useLang();
  return (
    <p className="flex items-center justify-center gap-2 py-24 text-muted">
      <Loader2 className="size-4 animate-spin" /> {t("loading")}
    </p>
  );
}
