"use client";

import { API_URL } from "@/lib/api";

export function useCamera(room?: string) {
  const target = room && room.trim() ? room.trim() : "default";
  return {
    streamUrl: `${API_URL}/api/v1/vision/stream/${encodeURIComponent(target)}`,
    describeUrl: `${API_URL}/api/v1/vision/describe`,
  };
}
