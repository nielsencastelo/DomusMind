"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Send, Trash2, Volume2 } from "lucide-react";
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

  function send(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    addMessage({ role: "user", content: text });
    addMessage({ role: "assistant", content: "" });
    setInput("");
    setBusy(true);
    setMeta("processando...");
    socket.send(text);
  }

  async function speakLastResponse() {
    const lastAssistant = [...messages].reverse().find((message) => message.role === "assistant" && message.content.trim());
    if (!lastAssistant || speaking) return;
    setSpeaking(true);
    setMeta("gerando audio...");
    try {
      const result = await api.speak(lastAssistant.content);
      setMeta(result.message);
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
