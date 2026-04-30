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
  created_at: string;
};

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

export const api = {
  health: () => request<HealthResponse>("/api/v1/health"),
  rooms: () => request<Room[]>("/api/v1/devices/rooms"),
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
};
