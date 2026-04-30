"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Camera, CheckCircle2, Play, Plus, RefreshCw, Search } from "lucide-react";
import { API_URL, api, Camera as CameraType, Room } from "@/lib/api";

function buildHikvisionUrl(form: CameraForm) {
  const user = encodeURIComponent(form.username.trim());
  const password = encodeURIComponent(form.password.trim());
  const auth = user || password ? `${user}:${password}@` : "";
  const channel = form.channel.trim() || "101";
  return `rtsp://${auth}${form.ip.trim()}:${form.port || 554}/Streaming/Channels/${channel}`;
}

type CameraForm = {
  name: string;
  roomName: string;
  ip: string;
  port: number;
  username: string;
  password: string;
  channel: string;
  isDefault: boolean;
};

const initialForm: CameraForm = {
  name: "Hikvision principal",
  roomName: "entrada",
  ip: "192.168.2.218",
  port: 554,
  username: "",
  password: "",
  channel: "101",
  isDefault: true,
};

export default function VisionPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [cameras, setCameras] = useState<CameraType[]>([]);
  const [selectedRoom, setSelectedRoom] = useState("");
  const [selectedCamera, setSelectedCamera] = useState<CameraType | null>(null);
  const [form, setForm] = useState<CameraForm>(initialForm);
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    const nextRooms = await api.rooms();
    setRooms(nextRooms);
    const nextCameras = nextRooms.flatMap((room) => room.cameras);
    setCameras(nextCameras);
    if (!selectedCamera && nextCameras.length > 0) {
      setSelectedCamera(nextCameras.find((camera) => camera.is_default) ?? nextCameras[0]);
      const room = nextRooms.find((item) => item.cameras.some((camera) => camera.id === nextCameras[0].id));
      setSelectedRoom(room?.name ?? "");
    }
  }

  useEffect(() => {
    load().catch(() => setMessage("Nao foi possivel carregar cameras."));
  }, []);

  const previewUrl = useMemo(() => buildHikvisionUrl(form), [form]);
  const streamUrl = selectedRoom ? `${API_URL}/api/v1/vision/stream/${selectedRoom}` : `${API_URL}/api/v1/vision/stream/default`;

  async function saveCamera(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      const camera = await api.createIpCamera({
        name: form.name,
        ip: form.ip,
        room_name: form.roomName,
        port: form.port,
        username: form.username || undefined,
        password: form.password || undefined,
        channel: form.channel,
        is_default: form.isDefault,
      });
      setSelectedCamera(camera);
      setSelectedRoom(form.roomName.trim().toLowerCase());
      setMessage("Camera IP salva.");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar camera.");
    }
  }

  async function testSource(source: string) {
    setBusy(true);
    setMessage("Testando captura...");
    try {
      const result = await api.testVisionSource(source);
      setMessage(result.message);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao testar camera.");
    } finally {
      setBusy(false);
    }
  }

  async function analyze(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setDescription("");
    try {
      const data = await api.describeVision(selectedRoom || null);
      setDescription(data.description ?? "Sem descricao.");
    } catch {
      setDescription("Nao foi possivel analisar a camera.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-5">
      <div className="flex flex-col justify-between gap-3 lg:flex-row lg:items-end">
        <div>
          <div className="chip mb-3">Cameras IP e visao computacional</div>
          <h1 className="page-title">Central de visao</h1>
          <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
            Cadastre cameras Hikvision por IP, valide a captura e envie a cena para analise.
          </p>
        </div>
        <button className="btn btn-secondary w-fit" onClick={() => load()}>
          <RefreshCw size={16} />
          Recarregar
        </button>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_24rem]">
        <div className="space-y-4">
          <div className="panel overflow-hidden">
            <div className="flex flex-col justify-between gap-3 border-b border-[var(--line)] px-4 py-3 md:flex-row md:items-center">
              <div className="flex items-center gap-2 font-medium">
                <Camera size={17} />
                {selectedCamera?.name || "camera padrao"}
              </div>
              <select
                className="control max-w-sm"
                value={selectedCamera?.id ?? ""}
                onChange={(event) => {
                  const camera = cameras.find((item) => item.id === event.target.value) ?? null;
                  setSelectedCamera(camera);
                  const room = rooms.find((item) => item.cameras.some((cam) => cam.id === camera?.id));
                  setSelectedRoom(room?.name ?? "");
                }}
              >
                <option value="">Padrao</option>
                {cameras.map((camera) => (
                  <option key={camera.id} value={camera.id}>
                    {camera.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="aspect-video bg-[#102022]">
              <img key={streamUrl} src={streamUrl} alt="Feed da camera" className="h-full w-full object-contain" />
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-[20rem_1fr]">
            <form onSubmit={analyze} className="panel space-y-3 p-4">
              <label>
                <span className="label">Comodo da analise</span>
                <select className="control" value={selectedRoom} onChange={(event) => setSelectedRoom(event.target.value)}>
                  <option value="">Padrao</option>
                  {rooms.map((room) => (
                    <option key={room.id} value={room.name}>
                      {room.friendly_name || room.name}
                    </option>
                  ))}
                </select>
              </label>
              <button className="btn btn-accent w-full" disabled={busy}>
                <Search size={16} />
                {busy ? "Processando" : "Analisar cena"}
              </button>
              {selectedCamera && (
                <button type="button" className="btn btn-secondary w-full" disabled={busy} onClick={() => testSource(selectedCamera.source_url)}>
                  <Play size={16} />
                  Testar camera salva
                </button>
              )}
            </form>

            <div className="panel p-4 text-sm leading-6 text-[var(--muted)]">
              <div className="mb-2 flex items-center gap-2 font-semibold text-[var(--ink)]">
                <CheckCircle2 size={16} />
                Resultado
              </div>
              {description || message || "A descricao da cena e os testes de conexao aparecem aqui."}
            </div>
          </div>
        </div>

        <aside className="panel h-fit p-4">
          <h2 className="mb-4 font-semibold">Nova camera Hikvision</h2>
          <form onSubmit={saveCamera} className="space-y-3">
            <label>
              <span className="label">Nome</span>
              <input className="control" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
            </label>
            <label>
              <span className="label">Comodo</span>
              <input className="control" value={form.roomName} onChange={(event) => setForm({ ...form, roomName: event.target.value })} />
            </label>
            <div className="grid grid-cols-[1fr_5.5rem] gap-2">
              <label>
                <span className="label">IP</span>
                <input className="control" value={form.ip} onChange={(event) => setForm({ ...form, ip: event.target.value })} />
              </label>
              <label>
                <span className="label">Porta</span>
                <input className="control" type="number" value={form.port} onChange={(event) => setForm({ ...form, port: Number(event.target.value) })} />
              </label>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <label>
                <span className="label">Usuario</span>
                <input className="control" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />
              </label>
              <label>
                <span className="label">Senha</span>
                <input className="control" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
              </label>
            </div>
            <label>
              <span className="label">Canal</span>
              <select className="control" value={form.channel} onChange={(event) => setForm({ ...form, channel: event.target.value })}>
                <option value="101">101 principal</option>
                <option value="102">102 substream</option>
                <option value="201">201 canal 2</option>
                <option value="202">202 canal 2 substream</option>
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm text-[var(--muted)]">
              <input type="checkbox" checked={form.isDefault} onChange={(event) => setForm({ ...form, isDefault: event.target.checked })} />
              Tornar padrao do comodo
            </label>
            <div className="break-all rounded-xl bg-[var(--soft)] p-3 text-xs text-[var(--muted)]">{previewUrl}</div>
            <div className="grid grid-cols-2 gap-2">
              <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => testSource(previewUrl)}>
                <Play size={16} />
                Testar
              </button>
              <button className="btn">
                <Plus size={16} />
                Salvar
              </button>
            </div>
          </form>
        </aside>
      </div>
    </section>
  );
}
