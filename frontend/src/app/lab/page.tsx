"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Bot, FlaskConical, RefreshCw, Send } from "lucide-react";
import { AgentKey, LlmConfig, ModelInfo, ProviderKey, api } from "@/lib/api";
import { useI18n } from "@/hooks/useI18n";
import { llmModelDescription } from "@/lib/modelInfo";

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
  const [config, setConfig] = useState<LlmConfig | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelMsg, setModelMsg] = useState("");
  const [response, setResponse] = useState("");
  const [providerUsed, setProviderUsed] = useState("");
  const [modelUsed, setModelUsed] = useState("");
  const [visionContext, setVisionContext] = useState("");
  const [searchContext, setSearchContext] = useState("");
  const [busy, setBusy] = useState(false);
  const { t } = useI18n();

  useEffect(() => {
    api.getLlmConfig().then(setConfig).catch(() => undefined);
  }, []);

  const effectiveProvider = useMemo<ProviderKey>(() => {
    return provider || config?.agents?.[agent]?.provider || "local";
  }, [agent, config, provider]);

  const configuredModel = config?.agents?.[agent]?.model || config?.providers?.[effectiveProvider]?.default_model || "";
  const effectiveModel = model.trim() || configuredModel;

  useEffect(() => {
    let active = true;
    setModels([]);
    setModelMsg("Carregando modelos...");
    api.llmModels(effectiveProvider)
      .then((result) => {
        if (!active) return;
        setModels(result.models);
        setModelMsg(result.ok ? `${result.models.length} modelo(s) disponivel(is) em ${effectiveProvider}.` : result.message);
      })
      .catch((err) => {
        if (!active) return;
        setModels([]);
        setModelMsg(err instanceof Error ? err.message : "Falha ao listar modelos.");
      });
    return () => {
      active = false;
    };
  }, [effectiveProvider]);

  async function loadModels(nextProvider = effectiveProvider) {
    setModelMsg("Carregando modelos...");
    try {
      const result = await api.llmModels(nextProvider);
      setModels(result.models);
      setModelMsg(result.ok ? `${result.models.length} modelo(s) disponivel(is) em ${nextProvider}.` : result.message);
    } catch (err) {
      setModelMsg(err instanceof Error ? err.message : "Falha ao listar modelos.");
      setModels([]);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setResponse("");
    setProviderUsed("");
    setModelUsed("");
    setVisionContext("");
    setSearchContext("");
    try {
      const result = await api.testAgent({
        agent,
        message,
        provider: provider || undefined,
        model: model.trim() || undefined,
        temperature,
      });
      setProviderUsed(result.provider_used);
      setModelUsed(result.model_used || "");
      setVisionContext(result.vision_context || "");
      setSearchContext(result.search_context || "");
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
        <h1 className="text-2xl font-semibold">{t("lab.title")}</h1>
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
                setProvider("");
                setModel("");
                setModels([]);
                setModelMsg("");
                setProviderUsed("");
                setModelUsed("");
                setVisionContext("");
                setSearchContext("");
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
          <p className="text-sm text-[var(--muted)]">
            {providerUsed
              ? `Provider usado: ${providerUsed}${modelUsed ? ` | modelo: ${modelUsed}` : ""}`
              : `Configurado: ${effectiveProvider}${effectiveModel ? ` | modelo: ${effectiveModel}` : ""}`}
          </p>
        </div>

        <form onSubmit={submit} className="grid gap-3 border-b border-[var(--line)] p-4 md:grid-cols-[1fr_1fr_8rem]">
          <label>
            <span className="label">Provider opcional</span>
            <select
              className="control"
              value={provider}
              onChange={(event) => {
                const next = event.target.value as ProviderKey | "";
                setProvider(next);
                setModel("");
                setModels([]);
                setModelMsg("");
              }}
            >
              <option value="">Configurado</option>
              <option value="local">Local/Ollama</option>
              <option value="gemini">Gemini</option>
              <option value="openai">OpenAI/GPT</option>
              <option value="claude">Claude</option>
            </select>
          </label>
          <label>
            <span className="label">Modelo opcional</span>
            <div className="flex gap-2">
              <input
                className="control"
                list="lab-agent-models"
                value={model}
                onChange={(event) => setModel(event.target.value)}
                placeholder={configuredModel || "Selecione ou use o configurado"}
              />
              <button type="button" className="btn btn-secondary px-3" onClick={() => loadModels()}>
                <RefreshCw size={15} />
              </button>
            </div>
            <datalist id="lab-agent-models">
              {models.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </datalist>
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
          {modelMsg && <p className="text-sm text-[var(--muted)] md:col-span-3">{modelMsg}</p>}
          {models.length > 0 && (
            <div className="grid max-h-44 gap-2 overflow-auto md:col-span-3 md:grid-cols-2 xl:grid-cols-3">
              {models.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`rounded-lg border px-3 py-2 text-left text-xs transition hover:bg-[var(--soft)] ${
                    effectiveModel === item.id ? "border-[var(--accent)] text-[var(--accent)]" : "border-[var(--line)]"
                  }`}
                  onClick={() => setModel(item.id)}
                >
                  <div className="truncate font-medium">{item.id}</div>
                  {item.name !== item.id && <div className="truncate text-[var(--muted)]">{item.name}</div>}
                  <div className="mt-1 line-clamp-2 leading-5 text-[var(--muted)]">
                    {llmModelDescription(effectiveProvider, item.id)}
                  </div>
                </button>
              ))}
            </div>
          )}
        </form>

        <div className="flex-1 overflow-y-auto p-4">
          {visionContext && (
            <div className="mb-3 max-w-4xl rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-4 text-sm leading-7">
              <div className="mb-2 font-semibold text-[var(--accent)]">Contexto real de visao usado</div>
              <div className="whitespace-pre-wrap text-[var(--muted)]">{visionContext}</div>
            </div>
          )}
          {searchContext && (
            <div className="mb-3 max-w-4xl rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-4 text-sm leading-7">
              <div className="mb-2 font-semibold text-[var(--accent)]">Pesquisa web real usada</div>
              <div className="whitespace-pre-wrap text-[var(--muted)]">{searchContext}</div>
            </div>
          )}
          <div className="max-w-4xl whitespace-pre-wrap rounded-2xl bg-[var(--soft)] p-4 text-sm leading-7">
            {response || "A resposta do agente aparece aqui."}
          </div>
        </div>
      </div>
    </section>
  );
}
