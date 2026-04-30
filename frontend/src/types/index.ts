export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  role: ChatRole;
  content: string;
};

export type StreamDonePayload = {
  intent?: string;
  provider?: string;
};

export type StreamEvent =
  | { type: "token"; data: string }
  | { type: "done"; data: StreamDonePayload }
  | { type: "error"; data: string };
