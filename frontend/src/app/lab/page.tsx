"use client";

import { FormEvent, useState } from "react";
import { Bot, FlaskConical, Send } from "lucide-react";
import { AgentKey, ProviderKey, api } from "@/lib/api";

const agents: Array<{ key: AgentKey; label: string; prompt: string }> = [
  { key: "geral", label: "Geral", prompt: "Explique o status ideal da casa em uma frase." },
  { key: "intent", label: "Classificador", prompt: "ligue a luz da sala" },
  { key: "visao", label: "Visao", prompt: "O que devo observar nesta imagem da camera?" },
  { key: "pesquisa", label: "Pesquisa", prompt: "Resuma estes resultados como se fossem uma busca web." },
  { key: "luz", label: "Automacao", prompt: "ligar a luz do escritorio" },
  { key: "memoria", label: "Memoria", prompt: "O que voce lembra sobre minhas preferencias?" },
];

export default function LabPage() {
  const [agent, setAgent] = useState<AgentKey>("geral");
  const [provider, setProvider] = useState<ProviderKey | "">("");
  const [model, setModel] = useState("");
  const [temperature, setTemperature] = useState(0.2);
  const [message, setMessage] = useState(agents[0].prompt);
  const [response, setResponse] = useState("");
  const [providerUsed, setProviderUsed] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setResponse("");
    setProviderUsed("");
    try {
      const result = await api.testAgent({
        agent,
        message,
        provider: provider || undefined,
        model: model.trim() || undefined,
        temperature,
      });
      setProviderUsed(result.provider_used);
      setResponse(result.response);
    } catch (err) {
      setResponse(err instanceof Error ? err.message : "Falha no teste do agente.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="grid min-h-[calc(100vh-3rem)] gap-4 xl:grid-cols-[20rem_1fr]">
      <aside className="panel h-fit p-4">
        <div className="chip mb-3">
          <FlaskConical size={14} />
          Ambiente de testes
        </div>
        <h1 className="text-2xl font-semibold">Laboratorio</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Teste cada agente sem depender do fluxo completo do chat.</p>

        <div className="mt-5 grid gap-2">
          {agents.map((item) => (
            <button
              key={item.key}
              className={`flex items-center justify-between rounded-xl border px-3 py-2 text-left text-sm transition ${
                agent === item.key ? "border-[var(--accent)] bg-[var(--soft)] text-[var(--ink)]" : "border-[var(--line)] text-[var(--muted)] hover:bg-[var(--soft)]"
              }`}
              onClick={() => {
                setAgent(item.key);
                setMessage(item.prompt);
              }}
            >
              {item.label}
              <Bot size={15} />
            </button>
          ))}
        </div>
      </aside>

      <div className="panel flex min-h-[34rem] flex-col overflow-hidden">
        <div className="border-b border-[var(--line)] px-4 py-3">
          <h2 className="font-semibold">Teste: {agents.find((item) => item.key === agent)?.label}</h2>
          <p className="text-sm text-[var(--muted)]">{providerUsed ? `Provider usado: ${providerUsed}` : "Use a configuracao salva ou force um provider abaixo."}</p>
        </div>

        <form onSubmit={submit} className="grid gap-3 border-b border-[var(--line)] p-4 md:grid-cols-[1fr_1fr_8rem]">
          <label>
            <span className="label">Provider opcional</span>
            <select className="control" value={provider} onChange={(event) => setProvider(event.target.value as ProviderKey | "")}>
              <option value="">Configurado</option>
              <option value="local">Local/Ollama</option>
              <option value="gemini">Gemini</option>
              <option value="openai">OpenAI/GPT</option>
              <option value="claude">Claude</option>
            </select>
          </label>
          <label>
            <span className="label">Modelo opcional</span>
            <input className="control" value={model} onChange={(event) => setModel(event.target.value)} placeholder="gemini-2.0-flash" />
          </label>
          <label>
            <span className="label">Temp.</span>
            <input className="control" type="number" min="0" max="1" step="0.1" value={temperature} onChange={(event) => setTemperature(Number(event.target.value))} />
          </label>
          <label className="md:col-span-3">
            <span className="label">Mensagem de teste</span>
            <textarea className="control min-h-28" value={message} onChange={(event) => setMessage(event.target.value)} />
          </label>
          <button className="btn btn-accent w-fit md:col-span-3" disabled={busy || !message.trim()}>
            <Send size={16} />
            {busy ? "Testando" : "Enviar teste"}
          </button>
        </form>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl whitespace-pre-wrap rounded-2xl bg-[var(--soft)] p-4 text-sm leading-7">
            {response || "A resposta do agente aparece aqui."}
          </div>
        </div>
      </div>
    </section>
  );
}
