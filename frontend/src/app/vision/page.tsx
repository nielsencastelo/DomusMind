"use client";

import { FormEvent, useEffect, useState } from "react";
import { Camera, RefreshCw, Search } from "lucide-react";
import { api, Room } from "@/lib/api";
import { useCamera } from "@/hooks/useCamera";

export default function VisionPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedRoom, setSelectedRoom] = useState("");
  const [manualRoom, setManualRoom] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const camera = useCamera(selectedRoom);

  useEffect(() => {
    api.rooms().then(setRooms).catch(() => setRooms([]));
  }, []);

  async function analyze(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setDescription("");
    try {
      const room = manualRoom.trim() || selectedRoom || null;
      const data = await api.describeVision(room);
      setDescription(data.description ?? "Sem descricao.");
    } catch {
      setDescription("Nao foi possivel analisar a camera.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-5">
      <div>
        <h1 className="page-title">Monitor de cameras</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Feed MJPEG via FastAPI e analise sob demanda por Gemini Vision ou YOLO.</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_22rem]">
        <div className="panel overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--line)] px-4 py-3">
            <div className="flex items-center gap-2 font-medium">
              <Camera size={17} />
              {selectedRoom || "camera padrao"}
            </div>
            <RefreshCw size={16} className="text-[var(--muted)]" />
          </div>
          <div className="aspect-video bg-[var(--ink)]">
            <img
              key={camera.streamUrl}
              src={camera.streamUrl}
              alt="Feed da camera"
              className="h-full w-full object-contain"
            />
          </div>
        </div>

        <div className="panel p-4">
          <form onSubmit={analyze} className="space-y-3">
            <label>
              <span className="label">Comodo</span>
              <select className="control" value={selectedRoom} onChange={(event) => setSelectedRoom(event.target.value)}>
                <option value="">Padrao</option>
                {rooms.map((room) => (
                  <option key={room.id} value={room.name}>
                    {room.friendly_name || room.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span className="label">Comodo manual</span>
              <input className="control" value={manualRoom} onChange={(event) => setManualRoom(event.target.value)} placeholder="escritorio" />
            </label>
            <button className="btn w-full" disabled={busy}>
              <Search size={16} />
              {busy ? "Analisando" : "Analisar cena"}
            </button>
          </form>
          <div className="mt-5 border-t border-[var(--line)] pt-4 text-sm leading-6 text-[var(--muted)]">
            {description || "A descricao da cena aparece aqui apos a analise."}
          </div>
        </div>
      </div>
    </section>
  );
}
