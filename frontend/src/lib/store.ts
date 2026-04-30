"use client";

import { create } from "zustand";
import type { ChatMessage } from "@/types";

type DomusState = {
  sessionId: string;
  messages: ChatMessage[];
  lastIntent: string;
  lastProvider: string;
  setSessionId: (sessionId: string) => void;
  addMessage: (message: ChatMessage) => void;
  appendAssistantToken: (token: string) => void;
  setRunMeta: (intent: string, provider: string) => void;
  clearMessages: () => void;
};

export const useDomusStore = create<DomusState>((set) => ({
  sessionId: "",
  messages: [],
  lastIntent: "",
  lastProvider: "",
  setSessionId: (sessionId) => set({ sessionId }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  appendAssistantToken: (token) =>
    set((state) => {
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last?.role === "assistant") {
        messages[messages.length - 1] = { ...last, content: last.content + token };
      }
      return { messages };
    }),
  setRunMeta: (lastIntent, lastProvider) => set({ lastIntent, lastProvider }),
  clearMessages: () => set({ messages: [], lastIntent: "", lastProvider: "" }),
}));
