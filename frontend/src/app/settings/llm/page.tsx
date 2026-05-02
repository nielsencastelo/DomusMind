"use client";

import { FormEvent, useEffect, useState } from "react";
import { Bot, RefreshCw, Save, Server, Sparkles } from "lucide-react";
import { api, LlmConfig, ModelInfo, ProviderKey } from "@/lib/api";
import { llmModelDescription } from "@/lib/modelInfo";
import { SettingsBackButton } from "@/components/SettingsBackButton";

const providers: Array<{ key: ProviderKey; label: string; hint: string }> = [
  { key: "gemini", label: "Gemini", hint: "Google AI Studio / Gemini API" },
  { key: "openai", label: "OpenAI / GPT", hint: "Modelos GPT via OpenAI API" },
  { key: "claude", label: "Claude", hint: "Anthropic Messages API" },
  { key: "local", label: "Ollama local", hint: "Modelos instalados no seu Ollama" },
];

function emptyConfig(): LlmConfig {
  return {
    providers: {
      local: { base_url: "http://host.docker.internal:11434", default_model: "phi4" },
      gemini: { api_key: "", default_model: "gemini-2.0-flash" },
      openai: { api_key: "", default_model: "gpt-4o" },
      claude: { api_key: "", default_model: "claude-sonnet-4-6" },
    },
    agents: {},
    embedding: { provider: "local", model: "nomic-embed-text" },
  };
}

export default function LlmProvidersPage() {
  const [config, setConfig] = useState<LlmConfig>(emptyConfig);
  const [models, setModels] = useState<Partial<Record<ProviderKey, ModelInfo[]>>>({});
  const [modelMessages, setModelMessages] = useState<Partial<Record<ProviderKey, string>>>({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getLlmConfig().then(setConfig).catch(() => undefined);
  }, []);

  function updateProvider(provider: ProviderKey, patch: Record<string, string>) {
    setConfig((current) => ({
      ...current,
      providers: {
        ...current.providers,
        [provider]: { ...(current.providers[provider] ?? {}), ...patch },
      },
    }));
  }

  async function loadModels(provider: ProviderKey) {
    setModelMessages((current) => ({ ...current, [provider]: "Carregando modelos..." }));
    try {
      const result = await api.llmModels(provider);
      setModels((current) => ({ ...current, [provider]: result.models }));
      setModelMessages((current) => ({
        ...current,
        [provider]: result.ok ? `${result.models.length} modelo(s) encontrado(s).` : result.message,
      }));
    } catch (err) {
      setModelMessages((current) => ({
        ...current,
        [provider]: err instanceof Error ? err.message : "Falha ao listar modelos.",
      }));
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const saved = await api.setLlmConfig(config);
      setConfig(saved);
      setMessage("Configuracoes de IA salvas.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar configuracoes.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-6">
      <SettingsBackButton />
      <div>
        <div className="chip mb-3"><Bot size={14} /> IA / LLM</div>
        <h1 className="page-title">Provedores e modelos</h1>
        <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
          Configure credenciais online, Ollama local e carregue a lista real de modelos disponiveis.
        </p>
      </div>

      <form onSubmit={save} className="space-y-4">
        <div className="grid gap-4 xl:grid-cols-2">
          {providers.map((provider) => {
            const cfg = config.providers[provider.key] ?? {};
            const availableModels = models[provider.key] ?? [];
            return (
              <article key={provider.key} className="panel p-5">
                <div className="mb-4 flex items-start justify-between gap-3">
                  <div>
                    <h2 className="flex items-center gap-2 font-semibold">
                      {provider.key === "local" ? <Server size={17} /> : <Sparkles size={17} />}
                      {provider.label}
                    </h2>
                    <p className="mt-1 text-sm text-[var(--muted)]">{provider.hint}</p>
                  </div>
                  <button type="button" className="btn btn-secondary px-3 py-1.5 text-xs" onClick={() => loadModels(provider.key)}>
                    <RefreshCw size={13} />
                    Modelos
                  </button>
                </div>

                <div className="space-y-3">
                  {provider.key === "local" ? (
                    <label>
                      <span className="label">OLLAMA_BASE_URL</span>
                      <input
                        className="control"
                        value={cfg.base_url ?? ""}
                        onChange={(event) => updateProvider(provider.key, { base_url: event.target.value })}
                      />
                    </label>
                  ) : (
                    <label>
                      <span className="label">API key</span>
                      <input
                        className="control"
                        type="password"
                        value={cfg.api_key ?? ""}
                        onChange={(event) => updateProvider(provider.key, { api_key: event.target.value })}
                        placeholder="Cole a chave do provedor"
                      />
                    </label>
                  )}

                  <label>
                    <span className="label">Modelo padrao</span>
                    <input
                      className="control"
                      list={`models-${provider.key}`}
                      value={cfg.default_model ?? ""}
                      onChange={(event) => updateProvider(provider.key, { default_model: event.target.value })}
                    />
                    <datalist id={`models-${provider.key}`}>
                      {availableModels.map((model) => (
                        <option key={model.id} value={model.id}>{model.name}</option>
                      ))}
                    </datalist>
                  </label>

                  {modelMessages[provider.key] && (
                    <p className="text-xs text-[var(--muted)]">{modelMessages[provider.key]}</p>
                  )}

                  {availableModels.length > 0 && (
                    <div className="max-h-40 overflow-auto rounded-lg border border-[var(--line)]">
                      {availableModels.map((model) => (
                        <button
                          type="button"
                          key={model.id}
                          className="block w-full px-3 py-2 text-left text-xs hover:bg-[var(--soft)]"
                          onClick={() => updateProvider(provider.key, { default_model: model.id })}
                        >
                          <span className="font-medium">{model.id}</span>
                          {model.name !== model.id && <span className="ml-2 text-[var(--muted)]">{model.name}</span>}
                          <span className="mt-1 block leading-5 text-[var(--muted)]">
                            {llmModelDescription(provider.key, model.id)}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </article>
            );
          })}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button className="btn btn-accent" disabled={busy}>
            <Save size={16} />
            {busy ? "Salvando..." : "Salvar provedores"}
          </button>
          {message && <span className="text-sm text-[var(--muted)]">{message}</span>}
        </div>
      </form>
    </section>
  );
}
