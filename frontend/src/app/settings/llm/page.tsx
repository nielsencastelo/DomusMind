"use client";

import { FormEvent, useState } from "react";
import { Save } from "lucide-react";
import { api } from "@/lib/api";

export default function LlmSettingsPage() {
  const [chain, setChain] = useState("gemini,local,openai,claude");
  const [primary, setPrimary] = useState("gemini");
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await Promise.all([
        api.setConfig("llm.fallback_chain", chain, "Ordem de fallback dos provedores LLM"),
        api.setConfig("llm.primary_provider", primary, "Provedor preferido para respostas"),
      ]);
      setMessage("Configuracoes de LLM salvas.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar LLM.");
    }
  }

  return (
    <section className="max-w-3xl space-y-5">
      <div>
        <h1 className="page-title">LLM</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Preferencias persistidas para o roteador multi-provedor.</p>
      </div>
      <form onSubmit={submit} className="panel space-y-4 p-4">
        <label>
          <span className="label">Provedor primario</span>
          <select className="control" value={primary} onChange={(event) => setPrimary(event.target.value)}>
            <option value="gemini">Gemini</option>
            <option value="local">Ollama local</option>
            <option value="openai">OpenAI</option>
            <option value="claude">Claude</option>
          </select>
        </label>
        <label>
          <span className="label">Fallback chain</span>
          <input className="control" value={chain} onChange={(event) => setChain(event.target.value)} />
        </label>
        <button className="btn w-fit">
          <Save size={16} />
          Salvar
        </button>
        {message && <p className="text-sm text-[var(--muted)]">{message}</p>}
      </form>
    </section>
  );
}
