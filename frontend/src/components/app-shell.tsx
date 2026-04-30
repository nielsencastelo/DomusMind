"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  Camera,
  CircuitBoard,
  Database,
  Home,
  FlaskConical,
  MessageSquare,
  Settings,
  SlidersHorizontal,
} from "lucide-react";

const nav = [
  { href: "/", label: "Painel", icon: Home },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/vision", label: "Visao", icon: Camera },
  { href: "/lab", label: "Testes", icon: FlaskConical },
  { href: "/devices", label: "Dispositivos", icon: CircuitBoard },
  { href: "/memory", label: "Memoria", icon: Database },
  { href: "/settings", label: "Ajustes", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[var(--surface)] text-[var(--ink)]">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-[var(--line)] bg-[var(--panel)] px-4 py-5 shadow-[20px_0_60px_rgba(18,36,41,0.06)] lg:block">
        <Link href="/" className="flex items-center gap-3 px-2">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-[var(--accent)] text-white shadow-sm">
            <Bot size={20} />
          </span>
          <span>
            <strong className="block text-base">DomusMind</strong>
            <span className="text-xs text-[var(--muted)]">Casa, memoria e agentes</span>
          </span>
        </Link>
        <nav className="mt-8 space-y-1">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                  active ? "bg-[var(--ink)] text-[var(--surface)] shadow-sm" : "text-[var(--muted)] hover:bg-[var(--soft)] hover:text-[var(--ink)]"
                }`}
              >
                <Icon size={17} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-5 left-4 right-4 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-3 text-xs text-[var(--muted)]">
          <div className="mb-2 flex items-center gap-2 text-[var(--ink)]">
            <SlidersHorizontal size={14} />
            Gateway FastAPI
          </div>
          <div className="truncate">{process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}</div>
        </div>
      </aside>

      <header className="sticky top-0 z-10 border-b border-[var(--line)] bg-[var(--panel)]/90 px-3 py-2 backdrop-blur lg:hidden">
        <nav className="flex gap-1 overflow-x-auto">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`grid h-11 min-w-12 place-items-center rounded-xl ${active ? "bg-[var(--ink)] text-[var(--surface)]" : "text-[var(--muted)]"}`}
                title={item.label}
              >
                <Icon size={18} />
              </Link>
            );
          })}
        </nav>
      </header>

      <main className="lg:pl-64">
        <div className="mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 lg:px-8">{children}</div>
      </main>
    </div>
  );
}
