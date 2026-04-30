"use client";

import { FormEvent, useMemo, useRef, useState } from "react";
import { Send, Trash2 } from "lucide-react";
import { WS_URL } from "@/lib/api";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function ChatPage() {
  const sessionId = useMemo(() => crypto.randomUUID(), []);
  const wsRef = useRef<WebSocket | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [meta, setMeta] = useState("");
  const [busy, setBusy] = useState(false);

  function ensureSocket() {
    if (wsRef.current?.readyState === WebSocket.OPEN) return wsRef.current;

    const socket = new WebSocket(`${WS_URL}/api/v1/chat/ws/${sessionId}`);
    wsRef.current = socket;
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "token") {
        setMessages((items) => {
          const copy = [...items];
          const last = copy[copy.length - 1];
          if (last?.role === "assistant") last.content += payload.data;
          return copy;
        });
      }
      if (payload.type === "done") {
        setBusy(false);
        setMeta(`intencao: ${payload.data.intent || "outro"} | provedor: ${payload.data.provider || "n/d"}`);
      }
      if (payload.type === "error") {
        setBusy(false);
        setMeta(payload.data);
      }
    };
    socket.onerror = () => {
      setBusy(false);
      setMeta("WebSocket indisponivel.");
    };
    return socket;
  }

  function send(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    const socket = ensureSocket();
    setMessages((items) => [...items, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setInput("");
    setBusy(true);
    setMeta("processando...");

    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ message: text }));
    } else {
      socket.onopen = () => socket.send(JSON.stringify({ message: text }));
    }
  }

  return (
    <section className="grid min-h-[calc(100vh-3rem)] gap-4 lg:grid-cols-[1fr_18rem]">
      <div className="flex min-h-[34rem] flex-col border border-[var(--line)] bg-[var(--panel)]">
        <div className="border-b border-[var(--line)] px-4 py-3">
          <h1 className="text-xl font-semibold">Chat operacional</h1>
          <p className="text-sm text-[var(--muted)]">{meta || "WebSocket pronto para streaming."}</p>
        </div>
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.map((message, index) => (
            <div key={index} className={message.role === "user" ? "ml-auto max-w-[80%]" : "mr-auto max-w-[80%]"}>
              <div className={`px-3 py-2 text-sm ${message.role === "user" ? "bg-[var(--ink)] text-[var(--surface)]" : "bg-[var(--soft)]"}`}>
                {message.content || " "}
              </div>
            </div>
          ))}
          {messages.length === 0 && <div className="text-sm text-[var(--muted)]">Envie um comando, pergunta ou pedido de automacao.</div>}
        </div>
        <form onSubmit={send} className="flex gap-2 border-t border-[var(--line)] p-3">
          <input className="control" value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ex: liga a luz da sala" />
          <button className="btn" disabled={busy} title="Enviar">
            <Send size={16} />
          </button>
        </form>
      </div>

      <aside className="panel p-4">
        <h2 className="mb-3 font-semibold">Sessao</h2>
        <p className="break-all text-xs text-[var(--muted)]">{sessionId}</p>
        <button className="btn btn-secondary mt-5 w-full" onClick={() => setMessages([])}>
          <Trash2 size={16} />
          Limpar
        </button>
      </aside>
    </section>
  );
}
