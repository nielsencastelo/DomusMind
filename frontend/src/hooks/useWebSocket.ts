"use client";

import { useCallback, useRef, useState } from "react";
import { WS_URL } from "@/lib/api";
import type { StreamEvent } from "@/types";

type UseWebSocketOptions = {
  sessionId: string;
  onEvent: (event: StreamEvent) => void;
};

export function useWebSocket({ sessionId, onEvent }: UseWebSocketOptions) {
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return socketRef.current;

    const socket = new WebSocket(`${WS_URL}/api/v1/chat/ws/${sessionId}`);
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
      setError("");
    };
    socket.onclose = () => setConnected(false);
    socket.onerror = () => {
      setConnected(false);
      setError("WebSocket indisponivel.");
    };
    socket.onmessage = (event) => onEvent(JSON.parse(event.data) as StreamEvent);

    return socket;
  }, [onEvent, sessionId]);

  const send = useCallback(
    (message: string) => {
      const socket = connect();
      const payload = JSON.stringify({ message });
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(payload);
        return;
      }
      socket.onopen = () => {
        setConnected(true);
        setError("");
        socket.send(payload);
      };
    },
    [connect],
  );

  return { connected, error, send };
}
