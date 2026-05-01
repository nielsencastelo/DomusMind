"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  Bot,
  Camera,
  CircuitBoard,
  Cpu,
  Database,
  Home,
  FlaskConical,
  MessageSquare,
  Settings,
  SlidersHorizontal,
  Zap,
} from "lucide-react";
import { api, type ServiceStatus } from "@/lib/api";
import { useDomusStore } from "@/lib/store";
import { useI18n } from "@/hooks/useI18n";

const navItems = [
  { href: "/",         key: "nav.dashboard" as const, icon: Home },
  { href: "/chat",     key: "nav.chat"      as const, icon: MessageSquare },
  { href: "/vision",   key: "nav.vision"    as const, icon: Camera },
  { href: "/lab",      key: "nav.lab"       as const, icon: FlaskConical },
  { href: "/devices",  key: "nav.devices"   as const, icon: CircuitBoard },
  { href: "/memory",   key: "nav.memory"    as const, icon: Database },
  { href: "/settings", key: "nav.settings"  as const, icon: Settings },
];

const LOCALES = [
  { code: "pt" as const, label: "PT" },
  { code: "en" as const, label: "EN" },
  { code: "es" as const, label: "ES" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [compute, setCompute] = useState<ServiceStatus | null>(null);
  const { t, locale } = useI18n();
  const setLocale = useDomusStore((s) => s.setLocale);

  useEffect(() => {
    let mounted = true;

    async function loadCompute() {
      try {
        const health = await api.health();
        const nextCompute =
          health.services.find((s) => s.name === "compute") ??
          health.services.find((s) => s.name === "gpu") ??
          null;
        if (mounted) setCompute(nextCompute);
      } catch {
        if (mounted)
          setCompute({ name: "compute", ok: false, message: "Compute: aguardando backend" });
      }
    }

    loadCompute();
    const timer = window.setInterval(loadCompute, 30_000);
    return () => { mounted = false; window.clearInterval(timer); };
  }, []);

  const computeLabel = useMemo(() => {
    const msg = compute?.message ?? "Compute: verificando";
    return msg.replace("CUDA disponivel:", "GPU:");
  }, [compute]);

  const computeMode = computeLabel.toLowerCase().includes("gpu") ? "GPU" : "CPU";
  const isGpu = computeMode === "GPU";

  return (
    <div
      className="min-h-screen text-[var(--ink)]"
      style={{ background: "var(--surface)" }}
    >
      {/* ── Desktop Sidebar ──────────────────────────────── */}
      <aside
        className="fixed inset-y-0 left-0 z-20 hidden w-64 lg:flex flex-col"
        style={{
          background: "linear-gradient(180deg, rgba(8,16,34,0.98) 0%, rgba(5,11,24,0.98) 100%)",
          borderRight: "1px solid rgba(0,180,220,0.1)",
          boxShadow: "4px 0 40px rgba(0,0,0,0.5), inset -1px 0 0 rgba(0,212,255,0.04)",
          backdropFilter: "blur(24px)",
        }}
      >
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 px-5 py-5">
          <span
            className="grid h-10 w-10 place-items-center rounded-xl shadow-lg"
            style={{
              background: "linear-gradient(135deg, rgba(0,212,255,0.2), rgba(139,92,246,0.2))",
              border: "1px solid rgba(0,212,255,0.35)",
              boxShadow: "0 0 20px rgba(0,212,255,0.15)",
            }}
          >
            <Bot size={20} className="text-[var(--accent)]" />
          </span>
          <span>
            <strong
              className="block text-base"
              style={{
                background: "linear-gradient(90deg, #ddeeff, var(--accent))",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              DomusMind
            </strong>
            <span className="text-xs text-[var(--muted)]">{t("app.tagline")}</span>
          </span>
        </Link>

        {/* Neon divider */}
        <div style={{ height: 1, background: "linear-gradient(90deg, transparent, rgba(0,212,255,0.18), transparent)", margin: "0 12px" }} />

        {/* Nav */}
        <nav className="flex-1 mt-4 px-3 space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                  active
                    ? "nav-active"
                    : "text-[var(--muted)] hover:text-[var(--ink)] hover:bg-[rgba(0,212,255,0.05)]"
                }`}
              >
                <Icon size={17} />
                {t(item.key)}
              </Link>
            );
          })}
        </nav>

        {/* Bottom badges */}
        <div className="p-3 space-y-2">
          {/* Compute badge */}
          <button
            type="button"
            title={computeLabel}
            className="flex w-full items-center gap-2.5 rounded-xl p-3 text-left text-xs transition-all"
            style={{
              background: isGpu
                ? "linear-gradient(135deg, rgba(0,212,255,0.08), rgba(139,92,246,0.08))"
                : "rgba(10,18,36,0.6)",
              border: isGpu ? "1px solid rgba(0,212,255,0.25)" : "1px solid rgba(0,180,220,0.1)",
              boxShadow: isGpu ? "0 0 20px rgba(0,212,255,0.06)" : "none",
            }}
          >
            <span
              className="grid h-7 w-7 flex-shrink-0 place-items-center rounded-lg"
              style={{
                background: isGpu ? "rgba(0,212,255,0.12)" : "rgba(10,18,36,0.8)",
                border: isGpu ? "1px solid rgba(0,212,255,0.2)" : "1px solid rgba(0,180,220,0.08)",
              }}
            >
              {isGpu ? (
                <Zap size={13} className="text-[var(--accent)]" />
              ) : (
                <Cpu size={13} className="text-[var(--muted)]" />
              )}
            </span>
            <span className="min-w-0">
              <strong className={`block ${isGpu ? "text-[var(--accent)]" : "text-[var(--ink)]"}`}>
                {computeMode}
              </strong>
              <span className="block truncate text-[var(--muted)]">{computeLabel}</span>
            </span>
            {isGpu && (
              <span
                className="ml-auto h-2 w-2 rounded-full flex-shrink-0"
                style={{
                  background: "var(--good)",
                  boxShadow: "0 0 6px var(--good)",
                  animation: "pulse-ring 2s ease-in-out infinite",
                }}
              />
            )}
          </button>

          {/* Gateway badge */}
          <div
            className="rounded-xl p-3 text-xs"
            style={{
              background: "rgba(6,12,26,0.7)",
              border: "1px solid rgba(0,180,220,0.08)",
            }}
          >
            <div className="mb-1.5 flex items-center gap-2 font-medium text-[var(--muted)]">
              <SlidersHorizontal size={13} />
              Gateway FastAPI
            </div>
            <div className="truncate text-[var(--muted)] opacity-70">
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            </div>
          </div>
        </div>
      </aside>

      {/* ── Mobile Header ─────────────────────────────────── */}
      <header
        className="sticky top-0 z-10 px-3 py-2 lg:hidden"
        style={{
          background: "rgba(6,12,26,0.92)",
          borderBottom: "1px solid rgba(0,180,220,0.1)",
          backdropFilter: "blur(20px)",
        }}
      >
        <nav className="flex gap-1 overflow-x-auto">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`grid h-11 min-w-12 place-items-center rounded-xl transition-all ${
                  active ? "nav-active" : "text-[var(--muted)]"
                }`}
                title={item.label}
              >
                <Icon size={18} />
              </Link>
            );
          })}
          <button
            className="flex h-11 min-w-28 items-center gap-2 rounded-xl px-3 text-left text-xs text-[var(--muted)]"
            style={{ background: "rgba(10,18,36,0.7)", border: "1px solid rgba(0,180,220,0.1)" }}
            title={computeLabel}
            type="button"
          >
            <Cpu size={15} />
            <span className="truncate">{computeMode}</span>
          </button>
        </nav>
      </header>

      {/* ── Main Content ──────────────────────────────────── */}
      <main className="lg:pl-64">
        <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
