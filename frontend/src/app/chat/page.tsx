"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Mic, MicOff, Send, Trash2, Volume2 } from "lucide-react";
import { api } from "@/lib/api";
import { useDomusStore } from "@/lib/store";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useI18n } from "@/hooks/useI18n";
import type { StreamEvent } from "@/types";

export default function ChatPage() {
  const sessionId = useMemo(() => crypto.randomUUID(), []);
  const [input, setInput] = useState("");
  const [meta, setMeta] = useState("");
  const [busy, setBusy] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const messages = useDomusStore((state) => state.messages);
  const setSessionId = useDomusStore((state) => state.setSessionId);
  const addMessage = useDomusStore((state) => state.addMessage);
  const appendAssistantToken = useDomusStore((state) => state.appendAssistantToken);
  const setRunMeta = useDomusStore((state) => state.setRunMeta);
  const clearMessages = useDomusStore((state) => state.clearMessages);
  const { t } = useI18n();

  useEffect(() => {
    setSessionId(sessionId);
  }, [sessionId, setSessionId]);

  useEffect(() => {
    return () => {
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.onstop = null;
        recorder.stop();
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const handleStreamEvent = useCallback(
    (payload: StreamEvent) => {
      if (payload.type === "token") appendAssistantToken(payload.data);
      if (payload.type === "done") {
        const intent = payload.data.intent || "outro";
        const provider = payload.data.provider || "n/d";
        setBusy(false);
        setRunMeta(intent, provider);
        setMeta(`intencao: ${intent} | provedor: ${provider}`);
      }
      if (payload.type === "error") {
        setBusy(false);
        setMeta(payload.data);
      }
    },
    [appendAssistantToken, setRunMeta],
  );

  const socket = useWebSocket({ sessionId, onEvent: handleStreamEvent });

  const sendText = useCallback(
    (text: string) => {
      const clean = text.trim();
      if (!clean || busy) return;
      addMessage({ role: "user", content: clean });
      addMessage({ role: "assistant", content: "" });
      setInput("");
      setBusy(true);
      setMeta("processando...");
      socket.send(clean);
    },
    [addMessage, busy, socket],
  );

  function send(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    sendText(text);
  }

  async function toggleRecording() {
    if (recording) {
      recorderRef.current?.stop();
      setRecording(false);
      setMeta("transcrevendo audio...");
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setMeta("Gravacao de audio nao esta disponivel neste navegador.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        setTranscribing(true);
        try {
          const result = await api.transcribeAudio(blob, "pt");
          if (!result.text.trim()) {
            setMeta("Nao consegui identificar fala no audio.");
            return;
          }
          setInput(result.text);
          setMeta("audio transcrito, enviando...");
          sendText(result.text);
        } catch (err) {
          setMeta(err instanceof Error ? err.message : "Nao foi possivel transcrever o audio.");
        } finally {
          setTranscribing(false);
        }
      };

      recorder.start();
      setRecording(true);
      setMeta("gravando... clique novamente para parar.");
    } catch (err) {
      setMeta(err instanceof Error ? err.message : "Nao foi possivel acessar o microfone.");
    }
  }

  async function speakLastResponse() {
    const lastAssistant = [...messages].reverse().find((message) => message.role === "assistant" && message.content.trim());
    if (!lastAssistant || speaking) return;
    setSpeaking(true);
    setMeta("gerando audio...");
    try {
      const blob = await api.speechAudio(lastAssistant.content);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      audio.onerror = () => URL.revokeObjectURL(url);
      await audio.play();
      setMeta("audio reproduzido no navegador.");
    } catch (err) {
      setMeta(err instanceof Error ? err.message : "Nao foi possivel reproduzir audio.");
    } finally {
      setSpeaking(false);
    }
  }

  return (
    <section className="grid min-h-[calc(100vh-3rem)] gap-4 lg:grid-cols-[1fr_18rem]">
      <div className="flex min-h-[34rem] flex-col border border-[var(--line)] bg-[var(--panel)]">
        <div className="border-b border-[var(--line)] px-4 py-3">
          <h1 className="text-xl font-semibold">{t("chat.title")}</h1>
          <p className="text-sm text-[var(--muted)]">
            {meta || (socket.connected ? "WebSocket conectado." : socket.error || "WebSocket pronto para streaming.")}
          </p>
        </div>
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.map((message, index) => (
            <div key={index} className={message.role === "user" ? "ml-auto max-w-[80%]" : "mr-auto max-w-[80%]"}>
              <div className={`px-3 py-2 text-sm ${message.role === "user" ? "bg-[var(--ink)] text-[var(--surface)]" : "bg-[var(--soft)]"}`}>
                {message.content || " "}
              </div>
            </div>
          ))}
          {messages.length === 0 && <div className="text-sm text-[var(--muted)]">{t("chat.empty")}</div>}
        </div>
        <form onSubmit={send} className="flex gap-2 border-t border-[var(--line)] p-3">
          <input className="control" value={input} onChange={(event) => setInput(event.target.value)} placeholder={t("chat.placeholder")} />
          <button
            type="button"
            className={`btn btn-secondary ${recording ? "border-red-400 text-red-300" : ""}`}
            onClick={toggleRecording}
            disabled={transcribing || busy}
            title={recording ? "Parar gravacao" : "Gravar audio"}
          >
            {recording ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
          <button className="btn" disabled={busy} title={t("chat.send")}>
            <Send size={16} />
          </button>
        </form>
      </div>

      <aside className="panel p-4">
        <h2 className="mb-3 font-semibold">Sessao</h2>
        <p className="break-all text-xs text-[var(--muted)]">{sessionId}</p>
        <button className="btn btn-secondary mt-5 w-full" onClick={clearMessages}>
          <Trash2 size={16} />
          {t("chat.clear")}
        </button>
        <button className="btn btn-secondary mt-2 w-full" onClick={speakLastResponse} disabled={speaking || !messages.some((message) => message.role === "assistant" && message.content.trim())}>
          <Volume2 size={16} />
          {t("chat.speak")}
        </button>
      </aside>
    </section>
  );
}
