"use client";

import type { ElementType } from "react";
import { useEffect, useState } from "react";
import { Activity, Camera, Database, HomeIcon, RefreshCw } from "lucide-react";
import { api, HealthResponse, Room } from "@/lib/api";
import { StatusDot } from "@/components/status-dot";

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const [nextHealth, nextRooms] = await Promise.all([api.health(), api.rooms()]);
      setHealth(nextHealth);
      setRooms(nextRooms);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar painel.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  const devices = rooms.flatMap((room) => room.devices);
  const cameras = rooms.flatMap((room) => room.cameras);

  return (
    <section className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="page-title">Centro de comando</h1>
          <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
            Estado do backend, Redis, banco, Home Assistant, comodos e cameras configuradas.
          </p>
        </div>
        <button className="btn btn-secondary w-fit" onClick={load}>
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>

      {error && <div className="panel border-[var(--bad)] p-3 text-sm text-[var(--bad)]">{error}</div>}

      <div className="grid gap-3 md:grid-cols-4">
        <Metric icon={Activity} label="Servicos" value={health?.services.length ?? 0} />
        <Metric icon={HomeIcon} label="Comodos" value={rooms.length} />
        <Metric icon={Database} label="Dispositivos" value={devices.length} />
        <Metric icon={Camera} label="Cameras" value={cameras.length} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="panel p-4">
          <h2 className="mb-4 text-lg font-semibold">Saude dos servicos</h2>
          <div className="divide-y divide-[var(--line)]">
            {health?.services.map((service) => (
              <div key={service.name} className="flex items-start justify-between gap-4 py-3">
                <div>
                  <div className="font-medium">{service.name}</div>
                  <div className="mt-1 text-sm text-[var(--muted)]">{service.message}</div>
                </div>
                <StatusDot ok={service.ok} />
              </div>
            ))}
            {!health && <div className="py-8 text-sm text-[var(--muted)]">Carregando status...</div>}
          </div>
        </div>

        <div className="panel p-4">
          <h2 className="mb-4 text-lg font-semibold">Comodos ativos</h2>
          <div className="space-y-3">
            {rooms.map((room) => (
              <div key={room.id} className="border-b border-[var(--line)] pb-3 last:border-0">
                <div className="font-medium">{room.friendly_name || room.name}</div>
                <div className="mt-1 text-sm text-[var(--muted)]">
                  {room.devices.length} dispositivos, {room.cameras.length} cameras
                </div>
              </div>
            ))}
            {rooms.length === 0 && <p className="text-sm text-[var(--muted)]">Nenhum comodo cadastrado ainda.</p>}
          </div>
        </div>
      </div>
    </section>
  );
}

function Metric({ icon: Icon, label, value }: { icon: ElementType; label: string; value: number }) {
  return (
    <div className="panel p-4">
      <Icon size={18} className="mb-4 text-[var(--accent)]" />
      <div className="text-3xl font-semibold">{value}</div>
      <div className="mt-1 text-sm text-[var(--muted)]">{label}</div>
    </div>
  );
}
