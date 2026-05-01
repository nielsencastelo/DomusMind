"use client";

import { FormEvent, useEffect, useState } from "react";
import { BrainCircuit, RefreshCw, Save, SlidersHorizontal } from "lucide-react";
import { AgentConfig, AgentKey, api, LlmConfig, ModelInfo, ProviderKey } from "@/lib/api";

const agents: Array<{ key: AgentKey; label: string; hint: string }> = [
  { key: "geral", label: "Agente geral", hint: "Resposta final e conversa principal." },
  { key: "intent", label: "Classificador", hint: "Detecta a intencao antes do fluxo." },
  { key: "visao", label: "Visao", hint: "Responde usando contexto de camera." },
  { key: "pesquisa", label: "Pesquisa", hint: "Resume resultados de busca." },
  { key: "luz", label: "Automacao", hint: "Interpreta comandos de dispositivos." },
  { key: "memoria", label: "Memoria", hint: "Fluxos com contexto RAG." },
];

const providers: ProviderKey[] = ["local", "gemini", "openai", "claude"];

function fallbackConfig(): LlmConfig {
  return {
    providers: {
      local: { base_url: "http://host.docker.internal:11434", default_model: "phi4" },
      gemini: { default_model: "gemini-2.0-flash" },
      openai: { default_model: "gpt-4o" },
      claude: { default_model: "claude-sonnet-4-6" },
    },
    agents: Object.fromEntries(
      agents.map((agent) => [
        agent.key,
        { provider: agent.key === "intent" || agent.key === "luz" ? "local" : "gemini", model: agent.key === "intent" || agent.key === "luz" ? "phi4" : "gemini-2.0-flash", temperature: 0.2, fallback: ["local"] },
      ]),
    ) as Record<string, AgentConfig>,
    embedding: { provider: "local", model: "nomic-embed-text" },
  };
}

export default function AgentsSettingsPage() {
  const [config, setConfig] = useState<LlmConfig>(fallbackConfig);
  const [models, setModels] = useState<Partial<Record<ProviderKey, ModelInfo[]>>>({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getLlmConfig().then(setConfig).catch(() => undefined);
  }, []);

  function updateAgent(agent: AgentKey, patch: Partial<AgentConfig>) {
    setConfig((current) => ({
      ...current,
      agents: {
        ...current.agents,
        [agent]: { ...current.agents[agent], ...patch },
      },
    }));
  }

  async function loadProviderModels(provider: ProviderKey) {
    const result = await api.llmModels(provider);
    if (result.ok) setModels((current) => ({ ...current, [provider]: result.models }));
    else setMessage(result.message);
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const saved = await api.setLlmConfig(config);
      setConfig(saved);
      setMessage("Agentes salvos.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar agentes.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-6">
      <div>
        <div className="chip mb-3"><BrainCircuit size={14} /> Matriz de agentes</div>
        <h1 className="page-title">Agentes e modelos</h1>
        <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
          Defina qual IA cada agente usa, com modelo, temperatura e cadeia de fallback.
        </p>
      </div>

      <form onSubmit={save} className="space-y-4">
        <div className="grid gap-4 xl:grid-cols-2">
          {agents.map((agent) => {
            const cfg = config.agents[agent.key];
            const providerModels = models[cfg.provider] ?? [];
            return (
              <article key={agent.key} className="panel p-4">
                <div className="mb-4 flex items-start justify-between gap-3">
                  <div>
                    <h2 className="font-semibold">{agent.label}</h2>
                    <p className="mt-1 text-sm text-[var(--muted)]">{agent.hint}</p>
                  </div>
                  <SlidersHorizontal size={18} className="text-[var(--accent)]" />
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <label>
                    <span className="label">IA</span>
                    <select
                      className="control"
                      value={cfg.provider}
                      onChange={(event) => {
                        const provider = event.target.value as ProviderKey;
                        updateAgent(agent.key, {
                          provider,
                          model: config.providers[provider]?.default_model || "",
                        });
                      }}
                    >
                      {providers.map((provider) => (
                        <option key={provider} value={provider}>{provider}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span className="label">Temperatura</span>
                    <input
                      className="control"
                      type="number"
                      min="0"
                      max="1"
                      step="0.1"
                      value={cfg.temperature}
                      onChange={(event) => updateAgent(agent.key, { temperature: Number(event.target.value) })}
                    />
                  </label>
                  <label className="md:col-span-2">
                    <span className="label">Modelo</span>
                    <div className="flex gap-2">
                      <input
                        className="control"
                        list={`agent-models-${agent.key}`}
                        value={cfg.model}
                        onChange={(event) => updateAgent(agent.key, { model: event.target.value })}
                      />
                      <button type="button" className="btn btn-secondary px-3" onClick={() => loadProviderModels(cfg.provider)}>
                        <RefreshCw size={15} />
                      </button>
                    </div>
                    <datalist id={`agent-models-${agent.key}`}>
                      {providerModels.map((model) => (
                        <option key={model.id} value={model.id}>{model.name}</option>
                      ))}
                    </datalist>
                  </label>
                  <label className="md:col-span-2">
                    <span className="label">Fallback separado por virgula</span>
                    <input
                      className="control"
                      value={cfg.fallback.join(",")}
                      onChange={(event) =>
                        updateAgent(agent.key, {
                          fallback: event.target.value
                            .split(",")
                            .map((item) => item.trim())
                            .filter(Boolean) as ProviderKey[],
                        })
                      }
                    />
                  </label>
                </div>
              </article>
            );
          })}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button className="btn btn-accent" disabled={busy}>
            <Save size={16} />
            {busy ? "Salvando..." : "Salvar agentes"}
          </button>
          {message && <span className="text-sm text-[var(--muted)]">{message}</span>}
        </div>
      </form>
    </section>
  );
}
