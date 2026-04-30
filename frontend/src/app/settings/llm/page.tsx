"use client";

import { FormEvent, useEffect, useState } from "react";
import { Brain, Save, SlidersHorizontal } from "lucide-react";
import { AgentKey, ProviderKey, api } from "@/lib/api";

type AgentConfig = {
  provider: ProviderKey;
  model: string;
  temperature: number;
  fallback: ProviderKey[];
};

const agents: Array<{ key: AgentKey; label: string; hint: string }> = [
  { key: "geral", label: "Agente geral", hint: "Resposta final, comandos livres e conversa." },
  { key: "intent", label: "Classificador", hint: "Detecta intencao antes do fluxo principal." },
  { key: "visao", label: "Visao", hint: "Responde usando contexto de camera." },
  { key: "pesquisa", label: "Pesquisa", hint: "Resume resultados de busca." },
  { key: "luz", label: "Automacao", hint: "Interpreta e responde comandos de dispositivos." },
  { key: "memoria", label: "Memoria", hint: "Testes e respostas apoiadas em contexto RAG." },
];

const providerModels: Record<ProviderKey, string> = {
  local: "llama3.1",
  gemini: "gemini-2.0-flash",
  openai: "gpt-4o-mini",
  claude: "claude-3-5-haiku-latest",
};

function defaultConfig(provider: ProviderKey = "gemini"): AgentConfig {
  return {
    provider,
    model: providerModels[provider],
    temperature: 0.2,
    fallback: provider === "local" ? ["gemini", "openai"] : ["local", "openai", "claude"],
  };
}

export default function LlmSettingsPage() {
  const [configs, setConfigs] = useState<Record<AgentKey, AgentConfig>>(() =>
    Object.fromEntries(agents.map((agent) => [agent.key, defaultConfig(agent.key === "intent" ? "local" : "gemini")])) as Record<AgentKey, AgentConfig>,
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    api
      .config()
      .then((entries) => {
        const entry = entries.find((item) => item.key === "llm.agents");
        if (entry?.value && typeof entry.value === "object") {
          const value = entry.value as Partial<Record<AgentKey, Partial<AgentConfig>>>;
          setConfigs((current) => {
            const next = { ...current };
            for (const agent of agents) {
              next[agent.key] = { ...next[agent.key], ...(value[agent.key] ?? {}) };
            }
            return next;
          });
        }
      })
      .catch(() => undefined);
  }, []);

  function update(agent: AgentKey, patch: Partial<AgentConfig>) {
    setConfigs((current) => ({ ...current, [agent]: { ...current[agent], ...patch } }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await api.setConfig("llm.agents", configs, "Provider, modelo e fallback por agente do DomusMind");
      await api.setConfig("llm.primary_provider", configs.geral.provider, "Compatibilidade com o roteador LLM");
      await api.setConfig("llm.fallback_chain", configs.geral.fallback.join(","), "Fallback padrao");
      setMessage("Configuracoes de LLM salvas.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar LLM.");
    }
  }

  return (
    <section className="space-y-5">
      <div>
        <div className="chip mb-3">
          <Brain size={14} />
          Roteamento de modelos
        </div>
        <h1 className="page-title">LLM por agente</h1>
        <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
          Escolha modelos locais ou online para cada etapa do DomusMind, com fallback por agente.
        </p>
      </div>

      <form onSubmit={submit} className="space-y-4">
        <div className="grid gap-4 xl:grid-cols-2">
          {agents.map((agent) => {
            const config = configs[agent.key];
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
                    <span className="label">Provider</span>
                    <select
                      className="control"
                      value={config.provider}
                      onChange={(event) => {
                        const provider = event.target.value as ProviderKey;
                        update(agent.key, { provider, model: providerModels[provider] });
                      }}
                    >
                      <option value="local">Local/Ollama</option>
                      <option value="gemini">Gemini</option>
                      <option value="openai">OpenAI/GPT</option>
                      <option value="claude">Claude</option>
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
                      value={config.temperature}
                      onChange={(event) => update(agent.key, { temperature: Number(event.target.value) })}
                    />
                  </label>
                  <label className="md:col-span-2">
                    <span className="label">Modelo</span>
                    <input className="control" value={config.model} onChange={(event) => update(agent.key, { model: event.target.value })} />
                  </label>
                  <label className="md:col-span-2">
                    <span className="label">Fallback separado por virgula</span>
                    <input
                      className="control"
                      value={config.fallback.join(",")}
                      onChange={(event) =>
                        update(agent.key, {
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
          <button className="btn btn-accent">
            <Save size={16} />
            Salvar matriz LLM
          </button>
          {message && <span className="text-sm text-[var(--muted)]">{message}</span>}
        </div>
      </form>
    </section>
  );
}
