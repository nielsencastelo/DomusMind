export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export type ServiceStatus = {
  name: string;
  ok: boolean;
  message: string;
};

export type HealthResponse = {
  status: "ok" | "degraded";
  services: ServiceStatus[];
};

export type Room = {
  id: string;
  name: string;
  friendly_name: string | null;
  devices: Device[];
  cameras: Camera[];
  created_at: string;
};

export type Device = {
  id: string;
  room_id: string;
  name: string;
  entity_id: string;
  domain: string;
  device_type: string;
  config?: Record<string, unknown> | null;
  created_at: string;
};

export type Camera = {
  id: string;
  room_id: string;
  name: string;
  source_url: string;
  username?: string | null;
  password?: string | null;
  is_default: boolean;
  camera_type?: string;
  channel?: number | null;
  is_local?: boolean;
  device_path?: string | null;
  last_seen_at?: string | null;
  resolution?: string | null;
  created_at: string;
};

export type VisionConfig = {
  provider: "yolo" | "gemini";
  gemini_key_set: boolean;
  yolo_weights: string;
  yolo_confidence: number;
  yolo_frames: number;
};

export type CameraTestResult = {
  ok: boolean;
  message: string;
  latency_ms?: number | null;
  resolution?: string | null;
  fps?: number | null;
  snapshot_base64?: string | null;
};

export type LocalCamera = {
  index: number;
  device_path: string;
  resolution: string;
  source_url: string;
};

export type AgentKey = "geral" | "intent" | "visao" | "pesquisa" | "luz" | "memoria";
export type ProviderKey = "local" | "gemini" | "openai" | "claude";

export type Memory = {
  id: string;
  title: string | null;
  content: string;
  source: string;
  created_at: string;
};

export type HaState = {
  entity_id: string;
  state: string;
  attributes?: Record<string, unknown>;
  last_changed?: string;
  last_updated?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export type AppVersion = {
  version: string;
  name: string;
};

export const api = {
  health: () => request<HealthResponse>("/api/v1/health"),
  version: () => request<AppVersion>("/api/v1/health/version"),
  rooms: () => request<Room[]>("/api/v1/devices/rooms"),
  cameras: () => request<Camera[]>("/api/v1/devices/cameras"),
  createRoom: (payload: {
    name: string;
    friendly_name?: string;
    devices?: Array<Partial<Device>>;
    cameras?: Array<Partial<Camera>>;
  }) =>
    request<Room>("/api/v1/devices/rooms", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createIpCamera: (payload: {
    name: string;
    ip: string;
    room_name?: string;
    room_id?: string;
    port?: number;
    username?: string;
    password?: string;
    channel?: string;
    is_default?: boolean;
  }) =>
    request<Camera>("/api/v1/devices/cameras/ip", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  addCamera: (roomId: string, payload: Partial<Camera>) =>
    request<Camera>(`/api/v1/devices/rooms/${roomId}/cameras`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  toggleLight: (room: string, action: "on" | "off") =>
    request<{ ok: boolean; message: string }>("/api/v1/devices/light", {
      method: "POST",
      body: JSON.stringify({ room, action }),
    }),
  speak: (text: string) =>
    request<{ ok: boolean; message: string }>("/api/v1/chat/speech", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  describeVision: (room: string | null) =>
    request<{ ok: boolean; room: string | null; description: string }>("/api/v1/vision/describe", {
      method: "POST",
      body: JSON.stringify({ room }),
    }),
  testVisionSource: (source_url: string) =>
    request<{ ok: boolean; message: string }>("/api/v1/vision/test-source", {
      method: "POST",
      body: JSON.stringify({ source_url }),
    }),
  testAgent: (payload: {
    agent: AgentKey;
    message: string;
    provider?: ProviderKey;
    model?: string;
    temperature?: number;
  }) =>
    request<{ agent: string; provider_used: string; response: string }>("/api/v1/chat/test-agent", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  cachedHaStates: () => request<HaState[]>("/api/v1/devices/ha/cache"),
  roomsConfig: () => request<{ rooms: Record<string, unknown> }>("/api/v1/config/rooms"),
  updateRoomsConfig: (rooms: Record<string, unknown>) =>
    request<{ ok: boolean; message: string }>("/api/v1/config/rooms", {
      method: "POST",
      body: JSON.stringify({ rooms }),
    }),
  memories: () => request<Memory[]>("/api/v1/memory/memories"),
  documents: () => request<Array<{ id: string; filename: string; content: string }>>("/api/v1/memory/documents"),
  createDocument: (filename: string, content: string) =>
    request<{ id: string; filename: string; content: string }>("/api/v1/memory/documents", {
      method: "POST",
      body: JSON.stringify({ filename, content }),
    }),
  config: () => request<Array<{ key: string; value: unknown; description?: string | null }>>("/api/v1/config"),
  setConfig: (key: string, value: unknown, description?: string) =>
    request<{ key: string; value: unknown; description?: string | null }>(`/api/v1/config/${key}`, {
      method: "PUT",
      body: JSON.stringify({ value, description }),
    }),
  deleteCamera: (cameraId: string) =>
    request<{ ok: boolean; message: string }>(`/api/v1/devices/cameras/${cameraId}`, {
      method: "DELETE",
    }),
  getVisionConfig: () => request<VisionConfig>("/api/v1/vision/config"),
  setVisionConfig: (payload: {
    provider: string;
    gemini_api_key?: string;
    yolo_weights?: string;
    yolo_confidence?: number;
    yolo_frames?: number;
  }) =>
    request<VisionConfig>("/api/v1/vision/config", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  testCamera: (payload: { source_url: string; username?: string; password?: string }) =>
    request<CameraTestResult>("/api/v1/vision/test-camera", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  localCameras: () => request<LocalCamera[]>("/api/v1/vision/local-cameras"),
};
