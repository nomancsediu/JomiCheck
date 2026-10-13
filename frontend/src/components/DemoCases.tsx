"use client";

import { useEffect, useState } from "react";
import { api, type DemoCase } from "@/lib/api";

export function useDemoCases() {
  const [cases, setCases] = useState<DemoCase[] | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    api.demoCases().then(setCases).catch(() => setError(true));
  }, []);
  return { cases, error };
}
