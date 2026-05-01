"use client";

import type { ElementType } from "react";
import { useEffect, useState } from "react";
import { Activity, Camera, Database, HomeIcon, RefreshCw, Cpu, Wifi } from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { api, type HealthResponse, type Room } from "@/lib/api";
import { StatusDot } from "@/components/status-dot";
import { MindSphere } from "@/components/mind-sphere";
import { useI18n } from "@/hooks/useI18n";

// Mock activity data — shows what the chart looks like with real data
const ACTIVITY_DATA = [
  { time: "00h", requests: 12, agents: 4 },
  { time: "03h", requests: 5,  agents: 1 },
  { time: "06h", requests: 8,  agents: 2 },
  { time: "09h", requests: 34, agents: 9 },
  { time: "12h", requests: 52, agents: 15 },
  { time: "15h", requests: 47, agents: 12 },
  { time: "18h", requests: 61, agents: 18 },
  { time: "21h", requests: 39, agents: 11 },
  { time: "Agora", requests: 28, agents: 7 },
];

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const { t } = useI18n();

  async function load() {
    setError("");
    setLoading(true);
    try {
      const [nextHealth, nextRooms] = await Promise.all([api.health(), api.rooms()]);
      setHealth(nextHealth);
      setRooms(nextRooms);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar painel.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const devices = rooms.flatMap((r) => r.devices);
  const cameras = rooms.flatMap((r) => r.cameras);
  const healthyServices = health?.services.filter((s) => s.ok).length ?? 0;
  const totalServices = health?.services.length ?? 0;

  return (
    <section className="space-y-6">
      {/* ── Header ──────────────────────────────────────── */}
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: "var(--good)", boxShadow: "0 0 8px var(--good)" }}
            />
            <span className="text-xs font-medium text-[var(--muted)] uppercase tracking-widest">
              Sistema operacional
            </span>
          </div>
          <h1 className="page-title">{t("dashboard.title")}</h1>
          <p className="mt-2 max-w-xl text-sm text-[var(--muted)]">
            {t("dashboard.subtitle")}
          </p>
        </div>
        <button
          className="btn btn-secondary w-fit gap-2"
          onClick={load}
          disabled={loading}
          style={{ opacity: loading ? 0.6 : 1 }}
        >
          <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          {loading ? t("common.loading") : t("dashboard.refresh")}
        </button>
      </div>

      {error && (
        <div
          className="panel p-3 text-sm"
          style={{ borderColor: "var(--bad)", color: "var(--bad)" }}
        >
          {error}
        </div>
      )}

      {/* ── Metric Cards ─────────────────────────────────── */}
      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
        <Metric
          icon={Activity}
          label="Serviços"
          value={totalServices}
          sub={`${healthyServices} saudáveis`}
          color="var(--accent)"
        />
        <Metric
          icon={HomeIcon}
          label="Cômodos"
          value={rooms.length}
          sub="configurados"
          color="var(--accent-2)"
        />
        <Metric
          icon={Database}
          label="Dispositivos"
          value={devices.length}
          sub="registrados"
          color="var(--good)"
        />
        <Metric
          icon={Camera}
          label="Câmeras"
          value={cameras.length}
          sub="ativas"
          color="#f5a623"
        />
      </div>

      {/* ── Main Grid ─────────────────────────────────────── */}
      <div className="grid gap-4 xl:grid-cols-[1fr_380px]">

        {/* Left column */}
        <div className="space-y-4">

          {/* 3D Sphere Hero */}
          <div
            className="panel grid-bg relative overflow-hidden"
            style={{ minHeight: 320 }}
          >
            {/* Background glow blobs */}
            <div
              className="pointer-events-none absolute inset-0"
              style={{
                background:
                  "radial-gradient(ellipse at 30% 50%, rgba(0,212,255,0.06) 0%, transparent 60%), radial-gradient(ellipse at 70% 50%, rgba(139,92,246,0.06) 0%, transparent 60%)",
              }}
            />

            <div className="relative flex h-full flex-col items-center justify-center gap-4 p-6 md:flex-row">
              {/* Sphere */}
              <div className="relative h-72 w-72 flex-shrink-0">
                <MindSphere />
                {/* Center label */}
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-1">
                  <span
                    className="text-xs font-semibold uppercase tracking-widest"
                    style={{ color: "var(--accent)", opacity: 0.7 }}
                  >
                    DomusMind
                  </span>
                  <span
                    className="text-3xl font-black"
                    style={{
                      background: "linear-gradient(135deg, #fff, var(--accent))",
                      WebkitBackgroundClip: "text",
                      WebkitTextFillColor: "transparent",
                      backgroundClip: "text",
                    }}
                  >
                    {totalServices}
                  </span>
                  <span className="text-xs text-[var(--muted)]">nós ativos</span>
                </div>
              </div>

              {/* Stats beside sphere */}
              <div className="flex flex-col gap-3 text-center md:text-left">
                <h2
                  className="text-xl font-bold"
                  style={{
                    background: "linear-gradient(90deg, #ddeeff, var(--accent))",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                  }}
                >
                  Rede Neural
                </h2>
                <p className="max-w-xs text-sm text-[var(--muted)]">
                  Visualização em tempo real das conexões entre agentes, dispositivos e serviços do ecossistema DomusMind.
                </p>
                <div className="flex flex-wrap justify-center gap-2 md:justify-start">
                  {[
                    { label: "Agentes", val: "7", color: "var(--accent)" },
                    { label: "Saúde", val: `${Math.round((healthyServices / Math.max(totalServices, 1)) * 100)}%`, color: "var(--good)" },
                    { label: "Cômodos", val: String(rooms.length), color: "var(--accent-2)" },
                  ].map(({ label, val, color }) => (
                    <span
                      key={label}
                      className="rounded-xl px-3 py-1.5 text-sm font-semibold"
                      style={{
                        background: `color-mix(in srgb, ${color} 10%, rgba(10,18,36,0.8))`,
                        border: `1px solid color-mix(in srgb, ${color} 30%, transparent)`,
                        color,
                      }}
                    >
                      {val} <span className="font-normal opacity-70">{label}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Activity Chart */}
          <div className="panel p-5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-[var(--ink)]">Atividade — últimas 24h</h2>
                <p className="text-xs text-[var(--muted)]">Requisições e agentes invocados por hora</p>
              </div>
              <span
                className="rounded-lg px-2.5 py-1 text-xs font-medium"
                style={{
                  background: "rgba(0,212,255,0.1)",
                  border: "1px solid rgba(0,212,255,0.2)",
                  color: "var(--accent)",
                }}
              >
                Ao vivo
              </span>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={ACTIVITY_DATA} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
                <defs>
                  <linearGradient id="gradRequests" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#00d4ff" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradAgents" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#8b5cf6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,220,0.06)" />
                <XAxis
                  dataKey="time"
                  tick={{ fill: "#5a7090", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#5a7090", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "rgba(8,16,34,0.95)",
                    border: "1px solid rgba(0,212,255,0.2)",
                    borderRadius: "0.75rem",
                    color: "#c8d8f0",
                    fontSize: 12,
                  }}
                  cursor={{ stroke: "rgba(0,212,255,0.2)", strokeWidth: 1 }}
                />
                <Area
                  type="monotone"
                  dataKey="requests"
                  stroke="#00d4ff"
                  strokeWidth={2}
                  fill="url(#gradRequests)"
                  name="Requisições"
                  dot={false}
                  activeDot={{ r: 4, fill: "#00d4ff", strokeWidth: 0 }}
                />
                <Area
                  type="monotone"
                  dataKey="agents"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  fill="url(#gradAgents)"
                  name="Agentes"
                  dot={false}
                  activeDot={{ r: 4, fill: "#8b5cf6", strokeWidth: 0 }}
                />
              </AreaChart>
            </ResponsiveContainer>
            <div className="mt-3 flex gap-4 text-xs text-[var(--muted)]">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-3 rounded-sm" style={{ background: "#00d4ff", opacity: 0.8 }} />
                Requisições
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-3 rounded-sm" style={{ background: "#8b5cf6", opacity: 0.8 }} />
                Agentes
              </span>
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">

          {/* Service health */}
          <div className="panel p-4">
            <div className="mb-4 flex items-center gap-2">
              <Wifi size={15} className="text-[var(--accent)]" />
              <h2 className="font-semibold">{t("dashboard.services")}</h2>
              {health && (
                <span className="ml-auto text-xs text-[var(--muted)]">
                  {healthyServices}/{totalServices}
                </span>
              )}
            </div>

            {/* Health bar */}
            {health && (
              <div
                className="mb-4 h-1.5 w-full overflow-hidden rounded-full"
                style={{ background: "rgba(0,180,220,0.1)" }}
              >
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${(healthyServices / Math.max(totalServices, 1)) * 100}%`,
                    background: "linear-gradient(90deg, var(--good), var(--accent))",
                    boxShadow: "0 0 10px var(--good)",
                  }}
                />
              </div>
            )}

            <div className="space-y-0">
              {health?.services.map((service, i) => (
                <div
                  key={service.name}
                  className="flex items-start justify-between gap-3 py-2.5"
                  style={{
                    borderBottom: i < health.services.length - 1 ? "1px solid rgba(0,180,220,0.07)" : "none",
                  }}
                >
                  <div className="min-w-0">
                    <div className="text-sm font-medium capitalize">{service.name}</div>
                    <div className="mt-0.5 truncate text-xs text-[var(--muted)]">{service.message}</div>
                  </div>
                  <StatusDot ok={service.ok} />
                </div>
              ))}
              {!health && (
                <div className="flex flex-col gap-2 py-4">
                  {[1, 2, 3].map((n) => (
                    <div
                      key={n}
                      className="h-10 w-full animate-pulse rounded-lg"
                      style={{ background: "rgba(0,180,220,0.05)" }}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Rooms */}
          <div className="panel p-4">
            <div className="mb-4 flex items-center gap-2">
              <HomeIcon size={15} className="text-[var(--accent-2)]" />
              <h2 className="font-semibold">{t("dashboard.rooms")}</h2>
            </div>
            <div className="space-y-2">
              {rooms.map((room) => (
                <div
                  key={room.id}
                  className="flex items-center gap-3 rounded-xl p-3 transition-all"
                  style={{
                    background: "rgba(6,12,26,0.5)",
                    border: "1px solid rgba(0,180,220,0.08)",
                  }}
                >
                  <span
                    className="grid h-8 w-8 flex-shrink-0 place-items-center rounded-lg text-xs"
                    style={{
                      background: "rgba(139,92,246,0.1)",
                      border: "1px solid rgba(139,92,246,0.2)",
                      color: "var(--accent-2)",
                    }}
                  >
                    <HomeIcon size={14} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">
                      {room.friendly_name || room.name}
                    </div>
                    <div className="text-xs text-[var(--muted)]">
                      {room.devices.length} disp. · {room.cameras.length} câm.
                    </div>
                  </div>
                  <span
                    className="h-1.5 w-1.5 rounded-full flex-shrink-0"
                    style={{ background: "var(--good)", boxShadow: "0 0 5px var(--good)" }}
                  />
                </div>
              ))}
              {rooms.length === 0 && !loading && (
                <p className="py-4 text-center text-sm text-[var(--muted)]">
                  Nenhum cômodo cadastrado ainda.
                </p>
              )}
              {loading && (
                <div className="flex flex-col gap-2">
                  {[1, 2].map((n) => (
                    <div
                      key={n}
                      className="h-14 animate-pulse rounded-xl"
                      style={{ background: "rgba(0,180,220,0.04)" }}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Compute summary */}
          <div
            className="panel p-4"
            style={{
              background: "linear-gradient(135deg, rgba(0,212,255,0.04), rgba(139,92,246,0.04))",
            }}
          >
            <div className="flex items-center gap-2 mb-3">
              <Cpu size={14} className="text-[var(--accent)]" />
              <span className="text-sm font-semibold">Infraestrutura</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "Backend", value: "FastAPI", ok: true },
                { label: "Cache", value: "Redis", ok: !!health?.services.find(s => s.name === "redis")?.ok },
                { label: "Banco", value: "SQLite", ok: !!health?.services.find(s => s.name === "db" || s.name === "database")?.ok },
                { label: "HA", value: "Home Asst.", ok: !!health?.services.find(s => s.name === "home_assistant" || s.name === "ha")?.ok },
              ].map(({ label, value, ok }) => (
                <div
                  key={label}
                  className="rounded-lg p-2.5"
                  style={{
                    background: "rgba(6,12,26,0.6)",
                    border: "1px solid rgba(0,180,220,0.07)",
                  }}
                >
                  <div className="flex items-center justify-between gap-1 mb-0.5">
                    <span className="text-xs text-[var(--muted)]">{label}</span>
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{
                        background: ok ? "var(--good)" : "rgba(90,112,144,0.4)",
                        boxShadow: ok ? "0 0 4px var(--good)" : "none",
                      }}
                    />
                  </div>
                  <div className="text-xs font-semibold text-[var(--ink)]">{value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: ElementType;
  label: string;
  value: number;
  sub: string;
  color: string;
}) {
  return (
    <div
      className="panel relative overflow-hidden p-4 transition-all hover:-translate-y-0.5"
      style={{ cursor: "default" }}
    >
      {/* Background glow */}
      <div
        className="pointer-events-none absolute right-0 top-0 h-24 w-24 rounded-full opacity-30"
        style={{
          background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
          transform: "translate(30%, -30%)",
        }}
      />
      <div
        className="mb-3 grid h-9 w-9 place-items-center rounded-xl"
        style={{
          background: `color-mix(in srgb, ${color} 12%, rgba(10,18,36,0.8))`,
          border: `1px solid color-mix(in srgb, ${color} 25%, transparent)`,
        }}
      >
        <Icon size={17} style={{ color }} />
      </div>
      <div className="text-3xl font-black" style={{ color }}>
        {value}
      </div>
      <div className="mt-0.5 text-sm font-medium text-[var(--ink)]">{label}</div>
      <div className="text-xs text-[var(--muted)]">{sub}</div>
    </div>
  );
}
