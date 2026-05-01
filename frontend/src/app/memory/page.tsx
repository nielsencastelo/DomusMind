"use client";

import { FormEvent, useEffect, useState } from "react";
import { FilePlus, RefreshCw } from "lucide-react";
import { api, Memory } from "@/lib/api";
import { useI18n } from "@/hooks/useI18n";

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [filename, setFilename] = useState("");
  const [content, setContent] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    setMemories(await api.memories());
  }

  useEffect(() => {
    load().catch(() => setMemories([]));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await api.createDocument(filename || "nota.txt", content);
      setFilename("");
      setContent("");
      setMessage("Documento indexado.");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao indexar documento.");
    }
  }

  return (
    <section className="grid gap-5 lg:grid-cols-[1fr_24rem]">
      <div className="space-y-5">
        <div className="flex justify-between gap-4">
          <div>
            <h1 className="page-title">Memoria</h1>
            <p className="mt-2 text-sm text-[var(--muted)]">Memorias consolidadas e documentos indexados para RAG.</p>
          </div>
          <button className="btn btn-secondary h-fit" onClick={load}>
            <RefreshCw size={16} />
          </button>
        </div>
        <div className="space-y-3">
          {memories.map((memory) => (
            <article key={memory.id} className="panel p-4">
              <div className="mb-2 flex items-center justify-between gap-3 text-sm">
                <strong>{memory.title || memory.source}</strong>
                <span className="text-xs text-[var(--muted)]">{new Date(memory.created_at).toLocaleString("pt-BR")}</span>
              </div>
              <p className="text-sm leading-6 text-[var(--muted)]">{memory.content}</p>
            </article>
          ))}
          {memories.length === 0 && <div className="panel p-6 text-sm text-[var(--muted)]">Nenhuma memoria consolidada ainda.</div>}
        </div>
      </div>

      <aside className="panel h-fit p-4">
        <h2 className="mb-4 font-semibold">Adicionar documento</h2>
        <form onSubmit={submit} className="space-y-3">
          <label>
            <span className="label">Arquivo</span>
            <input className="control" value={filename} onChange={(event) => setFilename(event.target.value)} placeholder="manual-ar.txt" />
          </label>
          <label>
            <span className="label">Conteudo</span>
            <textarea className="control min-h-44" value={content} onChange={(event) => setContent(event.target.value)} />
          </label>
          <button className="btn w-full" disabled={!content.trim()}>
            <FilePlus size={16} />
            Indexar
          </button>
          {message && <p className="text-sm text-[var(--muted)]">{message}</p>}
        </form>
      </aside>
    </section>
  );
}
