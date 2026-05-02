"use client";

import { FormEvent, useEffect, useState } from "react";
import { Mic, Play, Save, Volume2 } from "lucide-react";
import { api, AudioConfig } from "@/lib/api";
import { SettingsBackButton } from "@/components/SettingsBackButton";

const defaultConfig: AudioConfig = {
  audio_sample_rate: 16000,
  whisper_model: "medium",
  whisper_compute_type: "float32",
  tts_model_name: "tts_models/multilingual/multi-dataset/xtts_v2",
  tts_speaker_wav: "models/Voz_Nielsen.wav",
  tts_language: "pt",
  tts_voice_ready: false,
};

export default function AudioSettingsPage() {
  const [config, setConfig] = useState<AudioConfig>(defaultConfig);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [testText, setTestText] = useState("O sistema de voz esta funcionando.");
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    api.getAudioConfig().then(setConfig).catch(() => setMessage("Nao foi possivel carregar audio."));
  }, []);

  function update<K extends keyof AudioConfig>(key: K, value: AudioConfig[K]) {
    setConfig((current) => ({ ...current, [key]: value }));
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const saved = await api.setAudioConfig(config);
      setConfig(saved);
      setMessage("Configuracoes de audio salvas.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar audio.");
    } finally {
      setBusy(false);
    }
  }

  async function testSpeech() {
    setSpeaking(true);
    setMessage("Gerando audio...");
    try {
      const blob = await api.speechAudio(testText);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      audio.onerror = () => URL.revokeObjectURL(url);
      await audio.play();
      setMessage("Audio reproduzido no navegador.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao gerar audio.");
    } finally {
      setSpeaking(false);
    }
  }

  return (
    <section className="max-w-3xl space-y-6">
      <SettingsBackButton />
      <div>
        <div className="chip mb-3">
          <Mic size={14} />
          Voz operacional
        </div>
        <h1 className="page-title">Audio e voz</h1>
        <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
          Configure transcricao com faster-whisper e fala com TTS. O chat grava no navegador, transcreve no backend e toca a resposta no navegador.
        </p>
      </div>

      <form onSubmit={save} className="space-y-5">
        <div className="panel p-5">
          <h2 className="mb-4 flex items-center gap-2 font-semibold">
            <Mic size={17} />
            Transcricao
          </h2>
          <div className="grid gap-4 md:grid-cols-3">
            <label>
              <span className="label">Modelo Whisper</span>
              <input className="control" value={config.whisper_model} onChange={(event) => update("whisper_model", event.target.value)} />
            </label>
            <label>
              <span className="label">Compute type</span>
              <select className="control" value={config.whisper_compute_type} onChange={(event) => update("whisper_compute_type", event.target.value)}>
                <option value="float32">float32</option>
                <option value="float16">float16</option>
                <option value="int8">int8</option>
              </select>
            </label>
            <label>
              <span className="label">Sample rate</span>
              <input className="control" type="number" min={8000} step={1000} value={config.audio_sample_rate} onChange={(event) => update("audio_sample_rate", Number(event.target.value))} />
            </label>
          </div>
        </div>

        <div className="panel p-5">
          <h2 className="mb-4 flex items-center gap-2 font-semibold">
            <Volume2 size={17} />
            Texto para voz
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            <label>
              <span className="label">Modelo TTS</span>
              <input className="control" value={config.tts_model_name} onChange={(event) => update("tts_model_name", event.target.value)} />
            </label>
            <label>
              <span className="label">Idioma</span>
              <input className="control" value={config.tts_language} onChange={(event) => update("tts_language", event.target.value)} />
            </label>
          </div>
          <label className="mt-4 block">
            <span className="label">Audio de referencia da voz</span>
            <input className="control" value={config.tts_speaker_wav} onChange={(event) => update("tts_speaker_wav", event.target.value)} />
            <span className={`mt-1 block text-xs ${config.tts_voice_ready ? "text-[var(--accent)]" : "text-red-400"}`}>
              {config.tts_voice_ready ? "Arquivo encontrado no container." : "Arquivo ainda nao encontrado no container."}
            </span>
          </label>
        </div>

        <div className="panel p-5">
          <h2 className="mb-4 flex items-center gap-2 font-semibold">
            <Play size={17} />
            Teste rapido
          </h2>
          <textarea className="control min-h-24" value={testText} onChange={(event) => setTestText(event.target.value)} />
          <button type="button" className="btn btn-secondary mt-3" onClick={testSpeech} disabled={speaking || !testText.trim()}>
            <Volume2 size={16} />
            {speaking ? "Gerando..." : "Testar fala"}
          </button>
        </div>

        <button className="btn w-full" disabled={busy}>
          <Save size={16} />
          {busy ? "Salvando..." : "Salvar audio"}
        </button>
        {message && <p className="text-sm text-[var(--muted)]">{message}</p>}
      </form>
    </section>
  );
}
