"use client";

import { Bot, Loader2, Send } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { useLang } from "@/lib/i18n";

type Msg = { role: "user" | "assistant"; text: string; source?: string };

const SUGGESTIONS = {
  bn: ["আমি কি এই জমি কিনব?", "নামজারি কী?", "হক-শুফা কী?", "ফারায়েজ অনুযায়ী অংশ কীভাবে হয়?"],
  en: ["Should I buy this land?", "What is mutation?", "What is pre-emption?", "How are Faraiz shares calculated?"],
};

export function AskPanel({ reportId }: { reportId: string }) {
  const { t, lang } = useLang();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function ask(question: string) {
    const q = question.trim();
    if (!q || busy) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setBusy(true);
    try {
      const res = await api.ask(reportId, q, lang);
      setMessages((m) => [...m, { role: "assistant", text: res.answer, source: res.source }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: t("error_generic") }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="no-print flex flex-col rounded-xl border border-line bg-white">
      <header className="flex items-center gap-2 border-b border-line px-4 py-3">
        <Bot className="size-5 text-brand-700" />
        <h2 className="font-semibold">{t("ask_title")}</h2>
      </header>
      <div className="max-h-96 min-h-32 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS[lang].map((s) => (
              <button
                key={s}
                onClick={() => ask(s)}
                className="rounded-full border border-line px-3 py-1 text-xs text-ink hover:border-brand-500 hover:bg-brand-50"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
            <div
              className={`max-w-[90%] whitespace-pre-line rounded-lg px-3 py-2 text-sm leading-relaxed ${
                m.role === "user" ? "bg-brand-700 text-white" : "bg-paper text-ink"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {busy && <Loader2 className="size-4 animate-spin text-muted" />}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
        className="flex gap-2 border-t border-line p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("ask_placeholder")}
          maxLength={500}
          className="flex-1 rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brand-500"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          aria-label={t("ask_send")}
          className="rounded-md bg-brand-700 px-3 text-white hover:bg-brand-800 disabled:bg-brand-200"
        >
          <Send className="size-4" />
        </button>
      </form>
    </section>
  );
}
