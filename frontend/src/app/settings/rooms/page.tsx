"use client";

import { FormEvent, useEffect, useState } from "react";
import { Home, Plus, RefreshCw, Save } from "lucide-react";
import { api, Room } from "@/lib/api";

export default function RoomsSettingsPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [name, setName] = useState("");
  const [friendlyName, setFriendlyName] = useState("");
  const [lightEntity, setLightEntity] = useState("");
  const [cameraUrl, setCameraUrl] = useState("");
  const [roomsJson, setRoomsJson] = useState("{}");
  const [message, setMessage] = useState("");

  async function load() {
    const [nextRooms, config] = await Promise.all([
      api.rooms(),
      api.roomsConfig().catch(() => ({ rooms: {} })),
    ]);
    setRooms(nextRooms);
    setRoomsJson(JSON.stringify(config.rooms, null, 2));
  }

  useEffect(() => {
    load().catch(() => setRooms([]));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    const devices = lightEntity
      ? [
          {
            name: "Luz principal",
            entity_id: lightEntity,
            domain: lightEntity.startsWith("switch.") ? "switch" : "light",
            device_type: "light",
          },
        ]
      : [];
    const cameras = cameraUrl
      ? [
          {
            name: "Camera principal",
            source_url: cameraUrl,
            is_default: true,
          },
        ]
      : [];
    try {
      await api.createRoom({ name, friendly_name: friendlyName, devices, cameras });
      setName("");
      setFriendlyName("");
      setLightEntity("");
      setCameraUrl("");
      setMessage("Comodo salvo.");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar comodo.");
    }
  }

  async function saveJsonConfig(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      const parsed = JSON.parse(roomsJson) as Record<string, unknown>;
      const result = await api.updateRoomsConfig(parsed);
      setMessage(result.message);
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "JSON invalido.");
    }
  }

  return (
    <section className="grid gap-5 lg:grid-cols-[1fr_24rem]">
      <div>
        <h1 className="page-title">Comodos</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Cadastro de comodos, luzes e cameras no banco.</p>
        <form onSubmit={saveJsonConfig} className="panel mt-5 space-y-3 p-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-semibold">Editor JSON</h2>
            <button type="button" className="btn btn-secondary" onClick={load}>
              <RefreshCw size={16} />
              Recarregar
            </button>
          </div>
          <textarea className="control min-h-80 font-mono text-sm" value={roomsJson} onChange={(event) => setRoomsJson(event.target.value)} />
          <button className="btn w-fit">
            <Save size={16} />
            Salvar JSON
          </button>
        </form>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {rooms.map((room) => (
            <article key={room.id} className="panel p-4">
              <div className="flex items-center gap-2 font-semibold">
                <Home size={17} />
                {room.friendly_name || room.name}
              </div>
              <div className="mt-3 text-sm text-[var(--muted)]">
                {room.devices.length} dispositivos, {room.cameras.length} cameras
              </div>
            </article>
          ))}
        </div>
      </div>

      <aside className="panel h-fit p-4">
        <h2 className="mb-4 font-semibold">Novo comodo</h2>
        <form onSubmit={submit} className="space-y-3">
          <label>
            <span className="label">Nome tecnico</span>
            <input className="control" value={name} onChange={(event) => setName(event.target.value)} placeholder="sala" />
          </label>
          <label>
            <span className="label">Nome amigavel</span>
            <input className="control" value={friendlyName} onChange={(event) => setFriendlyName(event.target.value)} placeholder="Sala" />
          </label>
          <label>
            <span className="label">Entidade de luz</span>
            <input className="control" value={lightEntity} onChange={(event) => setLightEntity(event.target.value)} placeholder="light.sala_principal" />
          </label>
          <label>
            <span className="label">URL da camera</span>
            <input className="control" value={cameraUrl} onChange={(event) => setCameraUrl(event.target.value)} placeholder="rtsp://..." />
          </label>
          <button className="btn w-full" disabled={!name.trim()}>
            <Plus size={16} />
            Salvar
          </button>
          {message && <p className="text-sm text-[var(--muted)]">{message}</p>}
        </form>
      </aside>
    </section>
  );
}
