export type SourceKind = "pdf" | "code" | "text";
export type RecordStatus = "uploaded" | "processing" | "ready" | "error" | "draft";
export type JobStatus = "queued" | "running" | "done" | "error";

export interface TeamUser {
  id: string;
  name: string;
}

export interface SourceItem {
  id: string;
  filename: string;
  source_type: SourceKind;
  size_bytes: number;
  created_at: string;
  status: RecordStatus;
  user_id: string;
  date_folder: string;
  relative_path: string;
  note_id: string | null;
}

export interface NoteItem {
  id: string;
  title: string;
  preview: string;
  markdown: string;
  source_ids: string[];
  created_at: string;
  status: RecordStatus;
  user_id: string;
  date_folder: string;
  relative_path: string;
}

export interface JobItem {
  id: string;
  kind: "upload" | "note";
  status: JobStatus;
  message: string;
  source_id: string | null;
  note_id: string | null;
  created_at: string;
  user_id: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  graph_available: boolean;
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    let detail = `${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

function withUser(path: string, userId: string) {
  const url = new URL(path, "http://local.invalid");
  url.searchParams.set("user_id", userId);
  return `${url.pathname}?${url.searchParams.toString()}`;
}

export const api = {
  health: () => request<HealthResponse>("/api/health"),
  users: () => request<TeamUser[]>("/api/users"),
  sources: (userId: string) => request<SourceItem[]>(withUser("/api/sources", userId)),
  notes: (userId: string) => request<NoteItem[]>(withUser("/api/notes", userId)),
  note: (id: string) => request<NoteItem>(`/api/notes/${id}`),
  jobs: (userId: string) => request<JobItem[]>(withUser("/api/jobs", userId)),
  createNote: (userId: string, title?: string) =>
    request<NoteItem>("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: title ?? "새 노트", user_id: userId }),
    }),
  uploadSource: async (userId: string, file: File) => {
    const data = new FormData();
    data.append("file", file);
    data.append("user_id", userId);
    return request<SourceItem>("/api/sources", { method: "POST", body: data });
  },
  chat: async (
    userId: string,
    message: string,
    history: ChatTurn[],
    onDelta: (text: string) => void,
  ) => {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ user_id: userId, message, history }),
    });
    if (!response.ok) {
      let detail = `${response.status}`;
      try {
        const body = (await response.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        /* ignore */
      }
      throw new Error(detail);
    }
    if (!response.body) {
      throw new Error("응답 본문이 없습니다.");
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let full = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload || payload === "[DONE]") continue;
        const parsed = JSON.parse(payload) as { delta?: string; error?: string };
        if (parsed.error) throw new Error(parsed.error);
        if (parsed.delta) {
          full += parsed.delta;
          onDelta(full);
        }
      }
    }
    return full;
  },
};
