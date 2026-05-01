"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  Camera,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  MonitorPlay,
  Play,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  Wifi,
  X,
} from "lucide-react";
import { API_URL, api, Camera as CameraType, CameraTestResult, LocalCamera, Room } from "@/lib/api";

function buildHikvisionUrl(ip: string, port: number, username: string, password: string, channel: string) {
  const user = encodeURIComponent(username.trim());
  const pass = encodeURIComponent(password.trim());
  const auth = user || pass ? `${user}:${pass}@` : "";
  return `rtsp://${auth}${ip.trim()}:${port}/Streaming/Channels/${channel || "101"}`;
}

type IpForm = {
  name: string;
  roomName: string;
  ip: string;
  port: number;
  username: string;
  password: string;
  channel: string;
  isDefault: boolean;
};

const emptyForm: IpForm = {
  name: "Camera principal",
  roomName: "",
  ip: "192.168.2.218",
  port: 554,
  username: "",
  password: "",
  channel: "101",
  isDefault: true,
};

type StreamModalProps = { source: string; name: string; onClose: () => void };

function StreamModal({ source, name, onClose }: StreamModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="relative w-full max-w-4xl rounded-2xl bg-[var(--surface)] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-[var(--line)] px-5 py-3">
          <span className="font-semibold">{name}</span>
          <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-[var(--soft)]">
            <X size={18} />
          </button>
        </div>
        <div className="aspect-video bg-black">
          <img src={source} alt={name} className="h-full w-full object-contain" />
        </div>
      </div>
    </div>
  );
}

export default function VisionPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [cameras, setCameras] = useState<CameraType[]>([]);
  const [localCameras, setLocalCameras] = useState<LocalCamera[]>([]);
  const [loadingLocal, setLoadingLocal] = useState(false);

  const [streamModal, setStreamModal] = useState<{ source: string; name: string } | null>(null);
  const [selectedRoom, setSelectedRoom] = useState("");
  const [description, setDescription] = useState("");
  const [analyzeBusy, setAnalyzeBusy] = useState(false);

  const [form, setForm] = useState<IpForm>(emptyForm);
  const [formOpen, setFormOpen] = useState(false);
  const [saveBusy, setSaveBusy] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");

  const [testResult, setTestResult] = useState<CameraTestResult | null>(null);
  const [testBusy, setTestBusy] = useState(false);

  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  async function load() {
    try {
      const nextRooms = await api.rooms();
      setRooms(nextRooms);
      setCameras(nextRooms.flatMap((r) => r.cameras));
    } catch {
      setMessage("Nao foi possivel carregar cameras.");
    }
  }

  async function scanLocal() {
    setLoadingLocal(true);
    try {
      setLocalCameras(await api.localCameras());
    } catch {
      setMessage("Falha ao escanear cameras locais.");
    } finally {
      setLoadingLocal(false);
    }
  }

  useEffect(() => {
    load();
    scanLocal();
  }, []);

  const previewUrl = buildHikvisionUrl(form.ip, form.port, form.username, form.password, form.channel);

  async function testCamera() {
    setTestBusy(true);
    setTestResult(null);
    try {
      const result = await api.testCamera({
        source_url: previewUrl,
        username: form.username || undefined,
        password: form.password || undefined,
      });
      setTestResult(result);
    } catch (err) {
      setTestResult({ ok: false, message: err instanceof Error ? err.message : "Falha ao testar." });
    } finally {
      setTestBusy(false);
    }
  }

  async function testExistingCamera(cam: CameraType) {
    setTestBusy(true);
    setTestResult(null);
    setMessage(`Testando ${cam.name}...`);
    try {
      const result = await api.testCamera({
        source_url: cam.source_url,
        username: cam.username ?? undefined,
        password: cam.password ?? undefined,
      });
      setTestResult(result);
      setMessage("");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao testar.");
    } finally {
      setTestBusy(false);
    }
  }

  async function saveCamera(event: FormEvent) {
    event.preventDefault();
    setSaveBusy(true);
    setSaveMsg("");
    try {
      await api.createIpCamera({
        name: form.name,
        ip: form.ip,
        room_name: form.roomName,
        port: form.port,
        username: form.username || undefined,
        password: form.password || undefined,
        channel: form.channel,
        is_default: form.isDefault,
      });
      setSaveMsg("Camera salva com sucesso.");
      setForm(emptyForm);
      setFormOpen(false);
      setTestResult(null);
      await load();
    } catch (err) {
      setSaveMsg(err instanceof Error ? err.message : "Falha ao salvar.");
    } finally {
      setSaveBusy(false);
    }
  }

  async function deleteCamera(id: string) {
    setDeleteId(id);
    try {
      await api.deleteCamera(id);
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao remover camera.");
    } finally {
      setDeleteId(null);
    }
  }

  async function analyze(event: FormEvent) {
    event.preventDefault();
    setAnalyzeBusy(true);
    setDescription("");
    try {
      const data = await api.describeVision(selectedRoom || null);
      setDescription(data.description ?? "Sem descricao.");
    } catch {
      setDescription("Nao foi possivel analisar a camera.");
    } finally {
      setAnalyzeBusy(false);
    }
  }

  return (
    <section className="space-y-6">
      {streamModal && (
        <StreamModal
          source={`${API_URL}/api/v1/vision/stream/${streamModal.source}`}
          name={streamModal.name}
          onClose={() => setStreamModal(null)}
        />
      )}

      <div className="flex flex-col justify-between gap-3 lg:flex-row lg:items-end">
        <div>
          <div className="chip mb-3">Cameras e visao computacional</div>
          <h1 className="page-title">Central de visao</h1>
          <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
            Gerencie cameras IP e locais, teste conexoes sem LLM e analise cenas com IA.
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-secondary" onClick={() => { load(); scanLocal(); }}>
            <RefreshCw size={16} />
            Recarregar
          </button>
          <button className="btn" onClick={() => setFormOpen((v) => !v)}>
            <Plus size={16} />
            Nova camera
          </button>
        </div>
      </div>

      {message && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
          {message}
          <button className="ml-3 underline" onClick={() => setMessage("")}>fechar</button>
        </div>
      )}

      {/* Add camera form */}
      {formOpen && (
        <div className="panel p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold flex items-center gap-2"><Plus size={16} />Nova camera Hikvision / RTSP</h2>
            <button onClick={() => setFormOpen(false)} className="rounded-lg p-1.5 hover:bg-[var(--soft)]">
              <X size={16} />
            </button>
          </div>
          <form onSubmit={saveCamera} className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-2">
              <label>
                <span className="label">Nome</span>
                <input className="control" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </label>
              <label>
                <span className="label">Comodo</span>
                <input className="control" value={form.roomName} onChange={(e) => setForm({ ...form, roomName: e.target.value })} placeholder="sala, entrada, garagem..." />
              </label>
            </div>
            <div className="grid gap-4 lg:grid-cols-[1fr_7rem_1fr_1fr]">
              <label>
                <span className="label">IP / Host</span>
                <input className="control" value={form.ip} onChange={(e) => setForm({ ...form, ip: e.target.value })} required />
              </label>
              <label>
                <span className="label">Porta</span>
                <input className="control" type="number" value={form.port} onChange={(e) => setForm({ ...form, port: Number(e.target.value) })} />
              </label>
              <label>
                <span className="label">Usuario</span>
                <input className="control" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
              </label>
              <label>
                <span className="label">Senha</span>
                <input className="control" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
              </label>
            </div>
            <div className="grid gap-4 lg:grid-cols-[12rem_1fr]">
              <label>
                <span className="label">Canal</span>
                <select className="control" value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })}>
                  <option value="101">101 — principal</option>
                  <option value="102">102 — substream</option>
                  <option value="201">201 — canal 2</option>
                  <option value="202">202 — canal 2 sub</option>
                </select>
              </label>
              <label className="flex items-center gap-2 mt-6 text-sm text-[var(--muted)]">
                <input type="checkbox" checked={form.isDefault} onChange={(e) => setForm({ ...form, isDefault: e.target.checked })} />
                Tornar camera padrao do comodo
              </label>
            </div>

            <div className="rounded-xl bg-[var(--soft)] px-3 py-2 text-xs break-all text-[var(--muted)]">
              {previewUrl}
            </div>

            {/* Test result */}
            {testResult && (
              <div className={`rounded-xl border p-4 space-y-3 ${testResult.ok ? "border-[var(--accent)]/30 bg-[var(--accent)]/5" : "border-red-500/30 bg-red-500/5"}`}>
                <div className={`flex items-center gap-2 font-medium text-sm ${testResult.ok ? "text-[var(--accent)]" : "text-red-400"}`}>
                  <CheckCircle2 size={15} />
                  {testResult.message}
                </div>
                {testResult.ok && (
                  <div className="grid grid-cols-3 gap-3 text-xs text-[var(--muted)]">
                    {testResult.resolution && <span>Resolucao: <strong>{testResult.resolution}</strong></span>}
                    {testResult.fps && <span>FPS: <strong>{testResult.fps}</strong></span>}
                    {testResult.latency_ms && <span>Latencia: <strong>{testResult.latency_ms}ms</strong></span>}
                  </div>
                )}
                {testResult.snapshot_base64 && (
                  <img src={testResult.snapshot_base64} alt="snapshot" className="w-full max-h-48 object-contain rounded-lg" />
                )}
              </div>
            )}

            <div className="flex gap-3">
              <button type="button" className="btn btn-secondary flex-1" disabled={testBusy} onClick={testCamera}>
                <Play size={16} />
                {testBusy ? "Testando..." : "Testar conexao"}
              </button>
              <button type="submit" className="btn flex-1" disabled={saveBusy}>
                <Plus size={16} />
                {saveBusy ? "Salvando..." : "Salvar camera"}
              </button>
            </div>
            {saveMsg && <p className="text-sm text-[var(--accent)]">{saveMsg}</p>}
          </form>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1fr_22rem]">
        <div className="space-y-5">
          {/* IP cameras list */}
          <div className="panel overflow-hidden">
            <div className="flex items-center gap-2 border-b border-[var(--line)] px-5 py-3 font-semibold">
              <Wifi size={16} />
              Cameras registradas ({cameras.length})
            </div>
            {cameras.length === 0 ? (
              <div className="p-8 text-center text-sm text-[var(--muted)]">
                Nenhuma camera cadastrada. Clique em "Nova camera" para adicionar.
              </div>
            ) : (
              <div className="divide-y divide-[var(--line)]">
                {cameras.map((cam) => {
                  const room = rooms.find((r) => r.cameras.some((c) => c.id === cam.id));
                  return (
                    <div key={cam.id} className="flex flex-col gap-3 p-4 md:flex-row md:items-center">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Camera size={15} className="text-[var(--accent)] shrink-0" />
                          <span className="font-medium truncate">{cam.name}</span>
                          {cam.is_default && (
                            <span className="rounded-full bg-[var(--accent)]/15 px-2 py-0.5 text-xs text-[var(--accent)]">padrao</span>
                          )}
                        </div>
                        <div className="mt-1 text-xs text-[var(--muted)] truncate">{cam.source_url}</div>
                        <div className="mt-1 flex gap-3 text-xs text-[var(--muted)]">
                          {room && <span>Comodo: {room.friendly_name || room.name}</span>}
                          {cam.resolution && <span>Resolucao: {cam.resolution}</span>}
                          {cam.last_seen_at && <span>Visto: {new Date(cam.last_seen_at).toLocaleString("pt-BR")}</span>}
                        </div>
                      </div>
                      <div className="flex shrink-0 gap-2">
                        <button
                          className="btn btn-secondary px-3 py-1.5 text-xs"
                          disabled={testBusy}
                          onClick={() => testExistingCamera(cam)}
                        >
                          <Play size={13} />
                          Testar
                        </button>
                        <button
                          className="btn btn-secondary px-3 py-1.5 text-xs"
                          onClick={() => setStreamModal({ source: room?.name ?? "default", name: cam.name })}
                        >
                          <MonitorPlay size={13} />
                          Stream
                        </button>
                        <button
                          className="rounded-lg border border-red-500/30 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 transition-colors"
                          disabled={deleteId === cam.id}
                          onClick={() => deleteCamera(cam.id)}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Local cameras */}
          <div className="panel overflow-hidden">
            <div className="flex items-center justify-between border-b border-[var(--line)] px-5 py-3">
              <div className="flex items-center gap-2 font-semibold">
                <Cpu size={16} />
                Cameras locais detectadas ({localCameras.length})
              </div>
              <button className="btn btn-secondary px-3 py-1.5 text-xs" disabled={loadingLocal} onClick={scanLocal}>
                <RefreshCw size={13} className={loadingLocal ? "animate-spin" : ""} />
                Escanear
              </button>
            </div>
            {localCameras.length === 0 ? (
              <div className="p-8 text-center text-sm text-[var(--muted)]">
                {loadingLocal ? "Escaneando dispositivos..." : "Nenhuma camera local detectada."}
              </div>
            ) : (
              <div className="divide-y divide-[var(--line)]">
                {localCameras.map((cam) => (
                  <div key={cam.index} className="flex items-center gap-4 p-4">
                    <div className="flex-1">
                      <div className="font-medium">Webcam #{cam.index}</div>
                      <div className="mt-0.5 text-xs text-[var(--muted)]">{cam.device_path} — {cam.resolution}</div>
                    </div>
                    <button
                      className="btn btn-secondary px-3 py-1.5 text-xs"
                      onClick={() => setForm({ ...emptyForm, name: `Webcam ${cam.index}`, ip: cam.source_url, channel: "" })}
                    >
                      <Plus size={13} />
                      Adicionar
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Scene analysis sidebar */}
        <aside className="space-y-4">
          <form onSubmit={analyze} className="panel p-5 space-y-4">
            <h2 className="flex items-center gap-2 font-semibold">
              <Search size={16} />
              Analise de cena
            </h2>
            <label>
              <span className="label">Comodo</span>
              <select className="control" value={selectedRoom} onChange={(e) => setSelectedRoom(e.target.value)}>
                <option value="">Camera padrao</option>
                {rooms.map((room) => (
                  <option key={room.id} value={room.name}>
                    {room.friendly_name || room.name}
                  </option>
                ))}
              </select>
            </label>
            <button className="btn btn-accent w-full" disabled={analyzeBusy}>
              <Search size={16} />
              {analyzeBusy ? "Processando..." : "Analisar com IA"}
            </button>
            {description && (
              <div className="rounded-xl bg-[var(--soft)] p-4 text-sm leading-6 text-[var(--muted)]">
                <div className="mb-2 flex items-center gap-2 font-semibold text-[var(--ink)]">
                  <CheckCircle2 size={14} />
                  Resultado
                </div>
                {description}
              </div>
            )}
          </form>

          {/* Live stream preview */}
          {cameras.length > 0 && (
            <div className="panel overflow-hidden">
              <div className="border-b border-[var(--line)] px-4 py-3 text-sm font-semibold flex items-center gap-2">
                <MonitorPlay size={15} />
                Stream ao vivo
              </div>
              <select
                className="control m-3"
                onChange={(e) => {
                  if (e.target.value) {
                    const room = rooms.find((r) => r.cameras.some((c) => c.id === e.target.value));
                    setSelectedRoom(room?.name ?? "");
                  }
                }}
              >
                <option value="">Selecione uma camera</option>
                {cameras.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              {selectedRoom && (
                <div className="aspect-video bg-black">
                  <img
                    key={selectedRoom}
                    src={`${API_URL}/api/v1/vision/stream/${selectedRoom}`}
                    alt="Live stream"
                    className="h-full w-full object-contain"
                  />
                </div>
              )}
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}
