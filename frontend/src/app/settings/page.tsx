"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { Save } from "lucide-react";
import { api } from "@/lib/api";

type ConfigEntry = {
  key: string;
  value: unknown;
  description?: string | null;
};

export default function SettingsPage() {
  const [entries, setEntries] = useState<ConfigEntry[]>([]);
  const [keyName, setKeyName] = useState("assistant.name");
  const [value, setValue] = useState('"DomusMind"');
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    setEntries(await api.config());
  }

  useEffect(() => {
    load().catch(() => setEntries([]));
  }, []);

  async function save(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    let parsed: unknown = value;
    try {
      parsed = JSON.parse(value);
    } catch {
      parsed = value;
    }
    try {
      await api.setConfig(keyName, parsed, description || undefined);
      setMessage("Configuracao salva.");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar.");
    }
  }

  return (
    <section className="grid gap-5 lg:grid-cols-[1fr_24rem]">
      <div>
        <h1 className="page-title">Configuracoes</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Chaves em banco para ajustes do assistente sem editar arquivos.</p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link className="btn btn-secondary" href="/settings/rooms">
            Comodos
          </Link>
          <Link className="btn btn-secondary" href="/settings/llm">
            LLM
          </Link>
          <Link className="btn btn-secondary" href="/settings/vision">
            Visao
          </Link>
        </div>
        <div className="mt-5 divide-y divide-[var(--line)] border border-[var(--line)] bg-[var(--panel)]">
          {entries.map((entry) => (
            <button
              key={entry.key}
              className="block w-full px-4 py-3 text-left hover:bg-[var(--soft)]"
              onClick={() => {
                setKeyName(entry.key);
                setValue(JSON.stringify(entry.value, null, 2));
                setDescription(entry.description || "");
              }}
            >
              <div className="font-medium">{entry.key}</div>
              <div className="mt-1 truncate text-sm text-[var(--muted)]">{JSON.stringify(entry.value)}</div>
            </button>
          ))}
          {entries.length === 0 && <div className="p-5 text-sm text-[var(--muted)]">Nenhuma configuracao salva ainda.</div>}
        </div>
      </div>

      <aside className="panel h-fit p-4">
        <h2 className="mb-4 font-semibold">Editar chave</h2>
        <form onSubmit={save} className="space-y-3">
          <label>
            <span className="label">Chave</span>
            <input className="control" value={keyName} onChange={(event) => setKeyName(event.target.value)} />
          </label>
          <label>
            <span className="label">Valor JSON</span>
            <textarea className="control min-h-36" value={value} onChange={(event) => setValue(event.target.value)} />
          </label>
          <label>
            <span className="label">Descricao</span>
            <input className="control" value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <button className="btn w-full">
            <Save size={16} />
            Salvar
          </button>
          {message && <p className="text-sm text-[var(--muted)]">{message}</p>}
        </form>
      </aside>
    </section>
  );
}
