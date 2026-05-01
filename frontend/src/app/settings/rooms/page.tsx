"use client";

import { FormEvent, useEffect, useState } from "react";
import { Camera, Home, Lightbulb, Plus, RefreshCw } from "lucide-react";
import { api, Room } from "@/lib/api";

export default function RoomsSettingsPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [name, setName] = useState("");
  const [friendlyName, setFriendlyName] = useState("");
  const [lightEntity, setLightEntity] = useState("");
  const [cameraUrl, setCameraUrl] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    setRooms(await api.rooms());
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
      setMessage("Comodo salvo no PostgreSQL.");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar comodo.");
    }
  }

  return (
    <section className="grid gap-5 lg:grid-cols-[1fr_24rem]">
      <div>
        <div className="flex items-end justify-between gap-3">
          <div>
            <h1 className="page-title">Comodos e dispositivos</h1>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Cadastro direto no PostgreSQL. Sem arquivos JSON de configuracao.
            </p>
          </div>
          <button className="btn btn-secondary w-fit" onClick={load}>
            <RefreshCw size={16} />
            Recarregar
          </button>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {rooms.map((room) => (
            <article key={room.id} className="panel p-4">
              <div className="flex items-center gap-2 font-semibold">
                <Home size={17} />
                {room.friendly_name || room.name}
              </div>
              <div className="mt-3 space-y-2 text-sm text-[var(--muted)]">
                <div className="flex items-center gap-2">
                  <Lightbulb size={14} />
                  {room.devices.length} dispositivo(s)
                </div>
                <div className="flex items-center gap-2">
                  <Camera size={14} />
                  {room.cameras.length} camera(s)
                </div>
              </div>
              {room.cameras.length > 0 && (
                <div className="mt-3 space-y-1 border-t border-[var(--line)] pt-3">
                  {room.cameras.map((camera) => (
                    <div key={camera.id} className="truncate text-xs text-[var(--muted)]">
                      {camera.name}: {camera.source_url}
                    </div>
                  ))}
                </div>
              )}
            </article>
          ))}
          {rooms.length === 0 && (
            <div className="panel p-5 text-sm text-[var(--muted)]">
              Nenhum comodo cadastrado ainda.
            </div>
          )}
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
            <input className="control" value={cameraUrl} onChange={(event) => setCameraUrl(event.target.value)} placeholder="rtsp://usuario:senha@ip:554/Streaming/channels/101/" />
          </label>
          <button className="btn w-full" disabled={!name.trim()}>
            <Plus size={16} />
            Salvar no banco
          </button>
          {message && <p className="text-sm text-[var(--muted)]">{message}</p>}
        </form>
      </aside>
    </section>
  );
}
