"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Database, RefreshCw, Save } from "lucide-react";
import { api, LlmConfig, ModelInfo } from "@/lib/api";
import { llmModelDescription } from "@/lib/modelInfo";
import { SettingsBackButton } from "@/components/SettingsBackButton";

function fallbackConfig(): LlmConfig {
  return {
    providers: {
      local: { base_url: "http://host.docker.internal:11434", default_model: "phi4" },
      gemini: { default_model: "gemini-2.0-flash" },
      openai: { default_model: "gpt-4o" },
      claude: { default_model: "claude-sonnet-4-6" },
    },
    agents: {},
    embedding: { provider: "local", model: "nomic-embed-text" },
  };
}

export default function EmbeddingsSettingsPage() {
  const [config, setConfig] = useState<LlmConfig>(fallbackConfig);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getLlmConfig().then(setConfig).catch(() => undefined);
  }, []);

  const embeddingModels = useMemo(() => {
    const preferred = models.filter((model) => /embed|nomic|bge|e5/i.test(model.id));
    return preferred.length ? preferred : models;
  }, [models]);

  async function loadOllamaModels() {
    setMessage("Carregando modelos do Ollama...");
    const result = await api.llmModels("local");
    if (result.ok) {
      setModels(result.models);
      setMessage(`${result.models.length} modelo(s) local(is) encontrado(s).`);
    } else {
      setMessage(result.message);
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const saved = await api.setLlmConfig(config);
      setConfig(saved);
      setMessage("Embeddings salvos.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar embeddings.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="max-w-3xl space-y-6">
      <SettingsBackButton />
      <div>
        <div className="chip mb-3"><Database size={14} /> Embeddings</div>
        <h1 className="page-title">Modelo de embeddings</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Escolha o modelo que transforma textos em vetores para memoria semantica e RAG.
        </p>
      </div>

      <form onSubmit={save} className="panel space-y-5 p-5">
        <div className="grid gap-4 md:grid-cols-2">
          <label>
            <span className="label">Provider</span>
            <select
              className="control"
              value={config.embedding.provider}
              onChange={(event) =>
                setConfig((current) => ({
                  ...current,
                  embedding: { ...current.embedding, provider: event.target.value as "local" | "google" },
                }))
              }
            >
              <option value="local">Ollama local</option>
              <option value="google">Google text-embedding</option>
            </select>
          </label>
          <label>
            <span className="label">Modelo</span>
            <input
              className="control"
              list="embedding-models"
              value={config.embedding.model}
              onChange={(event) =>
                setConfig((current) => ({
                  ...current,
                  embedding: { ...current.embedding, model: event.target.value },
                }))
              }
            />
            <datalist id="embedding-models">
              {embeddingModels.map((model) => (
                <option key={model.id} value={model.id}>{model.name}</option>
              ))}
            </datalist>
          </label>
        </div>

        <div className="flex flex-wrap gap-3">
          <button type="button" className="btn btn-secondary" onClick={loadOllamaModels}>
            <RefreshCw size={16} />
            Ver modelos Ollama
          </button>
          <button className="btn btn-accent" disabled={busy}>
            <Save size={16} />
            {busy ? "Salvando..." : "Salvar embeddings"}
          </button>
        </div>

        {message && <p className="text-sm text-[var(--muted)]">{message}</p>}

        {embeddingModels.length > 0 && (
          <div className="grid gap-2 md:grid-cols-2">
            {embeddingModels.map((model) => (
              <button
                type="button"
                key={model.id}
                className="rounded-lg border border-[var(--line)] p-3 text-left text-sm hover:bg-[var(--soft)]"
                onClick={() =>
                  setConfig((current) => ({
                    ...current,
                    embedding: { ...current.embedding, model: model.id },
                  }))
                }
              >
                <div className="font-medium">{model.id}</div>
                {model.name !== model.id && <div className="text-xs text-[var(--muted)]">{model.name}</div>}
                <div className="mt-1 text-xs leading-5 text-[var(--muted)]">
                  {llmModelDescription("local", model.id)}
                </div>
              </button>
            ))}
          </div>
        )}
      </form>
    </section>
  );
}
