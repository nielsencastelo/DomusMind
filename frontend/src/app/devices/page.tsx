"use client";

import { useEffect, useState } from "react";
import { Lightbulb, Power, PowerOff, RefreshCw } from "lucide-react";
import { api, HaState, Room } from "@/lib/api";

export default function DevicesPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [states, setStates] = useState<HaState[]>([]);
  const [message, setMessage] = useState("");

  async function load() {
    const [nextRooms, nextStates] = await Promise.all([
      api.rooms(),
      api.cachedHaStates().catch(() => []),
    ]);
    setRooms(nextRooms);
    setStates(nextStates);
  }

  useEffect(() => {
    load().catch(() => setRooms([]));
  }, []);

  async function toggle(room: string, action: "on" | "off") {
    setMessage("");
    try {
      const result = await api.toggleLight(room, action);
      setMessage(result.message);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao acionar dispositivo.");
    }
  }

  function stateFor(entityId: string) {
    return states.find((item) => item.entity_id === entityId)?.state;
  }

  return (
    <section className="space-y-5">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="page-title">Dispositivos</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">Controle rapido dos dispositivos cadastrados por comodo.</p>
        </div>
        <button className="btn btn-secondary w-fit" onClick={load}>
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>

      {message && <div className="panel p-3 text-sm">{message}</div>}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {rooms.map((room) => (
          <article key={room.id} className="panel p-4">
            <h2 className="text-lg font-semibold">{room.friendly_name || room.name}</h2>
            <div className="mt-4 space-y-3">
              {room.devices.map((device) => (
                <div key={device.id} className="flex items-center justify-between gap-3 border-t border-[var(--line)] pt-3">
                  <div>
                    <div className="flex items-center gap-2 font-medium">
                      <Lightbulb size={16} />
                      {device.name}
                    </div>
                    <div className="mt-1 text-xs text-[var(--muted)]">{device.entity_id}</div>
                    {stateFor(device.entity_id) && (
                      <div className="mt-1 text-xs text-[var(--accent)]">estado: {stateFor(device.entity_id)}</div>
                    )}
                  </div>
                  {device.device_type === "light" && (
                    <div className="flex gap-1">
                      <button className="btn btn-secondary" title="Ligar" onClick={() => toggle(room.name, "on")}>
                        <Power size={15} />
                      </button>
                      <button className="btn btn-secondary" title="Desligar" onClick={() => toggle(room.name, "off")}>
                        <PowerOff size={15} />
                      </button>
                    </div>
                  )}
                </div>
              ))}
              {room.devices.length === 0 && <p className="text-sm text-[var(--muted)]">Sem dispositivos cadastrados.</p>}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
