"use client";

import Link from "next/link";
import {
  Bot,
  BrainCircuit,
  Camera,
  Database,
  Home,
  KeyRound,
  Mic,
  MessageSquareText,
  Settings2,
} from "lucide-react";
import { useI18n } from "@/hooks/useI18n";

const sections = [
  {
    href: "/settings/llm",
    title: "IA / LLM",
    description: "Credenciais, modelos online, Ollama local e modelos disponiveis.",
    icon: Bot,
  },
  {
    href: "/settings/agents",
    title: "Agentes",
    description: "Escolha qual IA, modelo, temperatura e fallback cada agente usa.",
    icon: BrainCircuit,
  },
  {
    href: "/settings/embeddings",
    title: "Embeddings",
    description: "Configure Google ou Ollama local para memoria semantica e RAG.",
    icon: Database,
  },
  {
    href: "/settings/llm/test",
    title: "Testar IA",
    description: "Chat simples para testar conexao, resposta e erros dos modelos.",
    icon: MessageSquareText,
  },
  {
    href: "/settings/vision",
    title: "Visao",
    description: "Provider visual, Gemini Vision, YOLO, pesos e parametros.",
    icon: Camera,
  },
  {
    href: "/settings/audio",
    title: "Audio e voz",
    description: "Whisper, TTS, voz de referencia, idioma e teste de fala.",
    icon: Mic,
  },
  {
    href: "/settings/rooms",
    title: "Comodos e dispositivos",
    description: "Cadastro de comodos, luzes e cameras vinculadas.",
    icon: Home,
  },
  {
    href: "/settings/system",
    title: "Sistema avancado",
    description: "Editor bruto de chaves internas do banco system_config.",
    icon: Settings2,
  },
];

export default function SettingsPage() {
  const { t } = useI18n();

  return (
    <section className="space-y-6">
      <div>
        <div className="chip mb-3">
          <KeyRound size={14} />
          Configuracao operacional
        </div>
        <h1 className="page-title">{t("settings.title")}</h1>
        <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
          Ajuste modelos de IA, provedores, embeddings, visao e dispositivos em areas separadas.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sections.map(({ href, title, description, icon: Icon }) => (
          <Link key={href} href={href} className="panel block p-5 transition hover:-translate-y-0.5 hover:border-[var(--accent)]/40">
            <div className="mb-4 flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-lg bg-[var(--soft)] text-[var(--accent)]">
                <Icon size={19} />
              </span>
              <h2 className="font-semibold">{title}</h2>
            </div>
            <p className="text-sm leading-6 text-[var(--muted)]">{description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
