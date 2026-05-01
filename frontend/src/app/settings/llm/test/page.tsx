"use client";

import { FormEvent, useEffect, useState } from "react";
import { MessageSquareText, RefreshCw, Send } from "lucide-react";
import { api, LlmConfig, ModelInfo, ProviderKey } from "@/lib/api";

const providers: ProviderKey[] = ["local", "gemini", "openai", "claude"];

export default function LlmTestPage() {
  const [config, setConfig] = useState<LlmConfig | null>(null);
  const [provider, setProvider] = useState<ProviderKey>("local");
  const [model, setModel] = useState("phi4");
  const [temperature, setTemperature] = useState(0.2);
  const [message, setMessage] = useState("Responda em uma frase: voce esta conectado?");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [response, setResponse] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [modelMsg, setModelMsg] = useState("");

  useEffect(() => {
    api.getLlmConfig().then((cfg) => {
      setConfig(cfg);
      const defaultModel = cfg.providers.local?.default_model || "phi4";
      setModel(defaultModel);
    }).catch(() => undefined);
  }, []);

  function changeProvider(nextProvider: ProviderKey) {
    setProvider(nextProvider);
    setModel(config?.providers[nextProvider]?.default_model || "");
    setModels([]);
    setModelMsg("");
    setResponse("");
    setError("");
  }

  async function loadModels() {
    setModelMsg("Carregando modelos...");
    const result = await api.llmModels(provider);
    if (result.ok) {
      setModels(result.models);
      setModelMsg(`${result.models.length} modelo(s) encontrado(s).`);
    } else {
      setModelMsg(result.message);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setResponse("");
    setError("");
    try {
      const result = await api.testLlm({ provider, model, message, temperature });
      if (result.ok) {
        setResponse(result.response || "");
      } else {
        setError(result.error || "Falha desconhecida.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao testar modelo.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="grid gap-5 lg:grid-cols-[1fr_24rem]">
      <div className="space-y-5">
        <div>
          <div className="chip mb-3"><MessageSquareText size={14} /> Testar IA</div>
          <h1 className="page-title">Chat de diagnostico</h1>
          <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
            Envie uma mensagem simples para qualquer provedor/modelo e veja resposta ou erro bruto.
          </p>
        </div>

        <form onSubmit={submit} className="panel space-y-4 p-5">
          <div className="grid gap-4 md:grid-cols-[12rem_1fr_9rem]">
            <label>
              <span className="label">IA</span>
              <select className="control" value={provider} onChange={(event) => changeProvider(event.target.value as ProviderKey)}>
                {providers.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label>
              <span className="label">Modelo</span>
              <input className="control" list="llm-test-models" value={model} onChange={(event) => setModel(event.target.value)} />
              <datalist id="llm-test-models">
                {models.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </datalist>
            </label>
            <label>
              <span className="label">Temp.</span>
              <input className="control" type="number" min="0" max="1" step="0.1" value={temperature} onChange={(event) => setTemperature(Number(event.target.value))} />
            </label>
          </div>

          <label>
            <span className="label">Mensagem</span>
            <textarea className="control min-h-32" value={message} onChange={(event) => setMessage(event.target.value)} />
          </label>

          <div className="flex flex-wrap gap-3">
            <button type="button" className="btn btn-secondary" onClick={loadModels}>
              <RefreshCw size={16} />
              Listar modelos
            </button>
            <button className="btn btn-accent" disabled={busy || !model || !message.trim()}>
              <Send size={16} />
              {busy ? "Testando..." : "Enviar teste"}
            </button>
          </div>
          {modelMsg && <p className="text-sm text-[var(--muted)]">{modelMsg}</p>}
        </form>

        {response && (
          <div className="panel p-5">
            <h2 className="mb-3 font-semibold text-[var(--accent)]">Resposta</h2>
            <p className="whitespace-pre-wrap text-sm leading-6">{response}</p>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-5">
            <h2 className="mb-3 font-semibold text-red-300">Erro reportado pelo provedor</h2>
            <pre className="whitespace-pre-wrap text-sm text-red-100">{error}</pre>
          </div>
        )}
      </div>

      <aside className="panel h-fit p-4">
        <h2 className="mb-3 font-semibold">Modelos carregados</h2>
        <div className="max-h-[32rem] space-y-2 overflow-auto">
          {models.map((item) => (
            <button
              key={item.id}
              className="block w-full rounded-lg border border-[var(--line)] p-3 text-left text-xs hover:bg-[var(--soft)]"
              onClick={() => setModel(item.id)}
            >
              <div className="font-medium">{item.id}</div>
              {item.name !== item.id && <div className="text-[var(--muted)]">{item.name}</div>}
            </button>
          ))}
          {models.length === 0 && <p className="text-sm text-[var(--muted)]">Clique em Listar modelos.</p>}
        </div>
      </aside>
    </section>
  );
}
