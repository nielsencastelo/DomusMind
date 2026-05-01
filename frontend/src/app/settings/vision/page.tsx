"use client";

import { FormEvent, useEffect, useState } from "react";
import { Bot, Download, Eye, Key, RefreshCw, Save, Sliders } from "lucide-react";
import { api, VisionConfig, YoloModelInfo } from "@/lib/api";
import { useI18n } from "@/hooks/useI18n";

export default function VisionSettingsPage() {
  const [config, setConfig] = useState<VisionConfig | null>(null);
  const [provider, setProvider] = useState<"yolo" | "gemini">("gemini");
  const [geminiKey, setGeminiKey] = useState("");
  const [weights, setWeights] = useState("models/yolov8x.pt");
  const [confidence, setConfidence] = useState(0.6);
  const [frames, setFrames] = useState(10);
  const [busy, setBusy] = useState(false);
  const [downloadBusy, setDownloadBusy] = useState("");
  const [yoloModels, setYoloModels] = useState<YoloModelInfo[]>([]);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const { t } = useI18n();

  useEffect(() => {
    api
      .getVisionConfig()
      .then((cfg) => {
        setConfig(cfg);
        setProvider(cfg.provider);
        setWeights(cfg.yolo_weights);
        setConfidence(cfg.yolo_confidence);
        setFrames(cfg.yolo_frames);
      })
      .catch(() => setMessage("Nao foi possivel carregar configuracoes de visao."));
    loadYoloModels();
  }, []);

  async function loadYoloModels() {
    try {
      setYoloModels(await api.yoloModels());
    } catch {
      setYoloModels([]);
    }
  }

  async function downloadModel(model: string) {
    setDownloadBusy(model);
    setMessage("");
    setIsError(false);
    try {
      const result = await api.downloadYoloModel(model);
      if (!result.ok) {
        setIsError(true);
        setMessage(result.message);
        return;
      }
      if (result.path) setWeights(result.path);
      setMessage(result.message);
      await loadYoloModels();
    } catch (err) {
      setIsError(true);
      setMessage(err instanceof Error ? err.message : "Falha ao baixar modelo YOLO.");
    } finally {
      setDownloadBusy("");
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    setIsError(false);
    try {
      const updated = await api.setVisionConfig({
        provider,
        gemini_api_key: geminiKey || undefined,
        yolo_weights: weights,
        yolo_confidence: confidence,
        yolo_frames: frames,
      });
      setConfig(updated);
      setGeminiKey("");
      setMessage("Configuracoes salvas com sucesso.");
    } catch (err) {
      setIsError(true);
      setMessage(err instanceof Error ? err.message : "Falha ao salvar configuracoes.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="max-w-2xl space-y-6">
      <div>
        <div className="chip mb-3">{t("settings.vision.chip")}</div>
        <h1 className="page-title">{t("settings.vision.title")}</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          {t("settings.vision.subtitle")}
        </p>
      </div>

      <form onSubmit={save} className="space-y-5">
        {/* Provider selector */}
        <div className="panel p-5 space-y-4">
          <h2 className="flex items-center gap-2 font-semibold">
            <Bot size={17} />
            {t("settings.vision.provider")}
          </h2>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setProvider("gemini")}
              className={`rounded-xl border p-4 text-left transition-all ${
                provider === "gemini"
                  ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]"
                  : "border-[var(--line)] hover:border-[var(--accent)]/50"
              }`}
            >
              <div className="font-semibold">{t("settings.vision.gemini")}</div>
              <div className="mt-1 text-xs text-[var(--muted)]">{t("settings.vision.geminiDesc")}</div>
            </button>
            <button
              type="button"
              onClick={() => setProvider("yolo")}
              className={`rounded-xl border p-4 text-left transition-all ${
                provider === "yolo"
                  ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]"
                  : "border-[var(--line)] hover:border-[var(--accent)]/50"
              }`}
            >
              <div className="font-semibold">{t("settings.vision.yolo")}</div>
              <div className="mt-1 text-xs text-[var(--muted)]">{t("settings.vision.yoloDesc")}</div>
            </button>
          </div>

          {config && (
            <div className="flex items-center gap-2 rounded-lg bg-[var(--soft)] px-3 py-2 text-xs text-[var(--muted)]">
              <Eye size={13} />
              <span>Provedor atual: <strong className="text-[var(--ink)]">{config.provider}</strong></span>
              {config.provider === "gemini" && (
                <span className="ml-auto">{config.gemini_key_set ? "✓ Chave configurada" : "⚠ Chave nao configurada"}</span>
              )}
            </div>
          )}
        </div>

        {/* Gemini config */}
        {provider === "gemini" && (
          <div className="panel p-5 space-y-4">
            <h2 className="flex items-center gap-2 font-semibold">
              <Key size={17} />
              Credenciais Gemini
            </h2>
            <label>
              <span className="label">Google Gemini API Key</span>
              <input
                className="control"
                type="password"
                placeholder={config?.gemini_key_set ? "••••••••••••••••••• (ja configurada)" : "AIza..."}
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
              />
              <span className="mt-1 block text-xs text-[var(--muted)]">
                Deixe em branco para manter a chave atual. Disponivel em console.cloud.google.com.
              </span>
            </label>
          </div>
        )}

        {/* YOLO config */}
        {provider === "yolo" && (
          <div className="panel p-5 space-y-4">
            <h2 className="flex items-center gap-2 font-semibold">
              <Sliders size={17} />
              Parametros YOLO
            </h2>
            <label>
              <span className="label">Caminho dos pesos</span>
              <input
                className="control"
                value={weights}
                onChange={(e) => setWeights(e.target.value)}
                placeholder="models/yolov8x.pt"
              />
              <span className="mt-1 block text-xs text-[var(--muted)]">
                Caminho relativo ao diretorio /app dentro do container.
              </span>
            </label>
            <div className="rounded-xl border border-[var(--line)]">
              <div className="flex items-center justify-between gap-3 border-b border-[var(--line)] px-3 py-2">
                <span className="text-sm font-medium">Modelos YOLO</span>
                <button type="button" className="btn btn-secondary px-3 py-1.5 text-xs" onClick={loadYoloModels}>
                  <RefreshCw size={13} />
                  Atualizar
                </button>
              </div>
              <div className="divide-y divide-[var(--line)]">
                {yoloModels.map((model) => (
                  <div key={model.name} className="flex flex-col gap-2 px-3 py-3 sm:flex-row sm:items-center sm:justify-between">
                    <button
                      type="button"
                      className="min-w-0 text-left"
                      onClick={() => model.installed && setWeights(model.path)}
                    >
                      <div className="truncate text-sm font-medium">{model.name}</div>
                      <div className="text-xs text-[var(--muted)]">
                        {model.installed
                          ? `Instalado em ${model.path}${model.size_bytes ? ` (${(model.size_bytes / 1024 / 1024).toFixed(1)} MB)` : ""}`
                          : "Disponivel para download"}
                      </div>
                    </button>
                    {model.installed ? (
                      <button type="button" className="btn btn-secondary px-3 py-1.5 text-xs" onClick={() => setWeights(model.path)}>
                        Usar
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="btn btn-secondary px-3 py-1.5 text-xs"
                        disabled={!!downloadBusy}
                        onClick={() => downloadModel(model.name)}
                      >
                        <Download size={13} />
                        {downloadBusy === model.name ? "Baixando..." : "Baixar"}
                      </button>
                    )}
                  </div>
                ))}
                {yoloModels.length === 0 && (
                  <div className="px-3 py-4 text-sm text-[var(--muted)]">
                    Nenhum modelo listado. Verifique o backend.
                  </div>
                )}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <label>
                <span className="label">Confianca minima ({(confidence * 100).toFixed(0)}%)</span>
                <input
                  className="control"
                  type="range"
                  min={0.1}
                  max={0.95}
                  step={0.05}
                  value={confidence}
                  onChange={(e) => setConfidence(Number(e.target.value))}
                />
              </label>
              <label>
                <span className="label">Frames por analise</span>
                <input
                  className="control"
                  type="number"
                  min={1}
                  max={60}
                  value={frames}
                  onChange={(e) => setFrames(Number(e.target.value))}
                />
              </label>
            </div>
          </div>
        )}

        <button className="btn w-full" disabled={busy}>
          <Save size={16} />
          {busy ? t("settings.vision.saving") : t("settings.vision.saveBtn")}
        </button>

        {message && (
          <p className={`text-sm ${isError ? "text-red-400" : "text-[var(--accent)]"}`}>{message}</p>
        )}
      </form>
    </section>
  );
}
