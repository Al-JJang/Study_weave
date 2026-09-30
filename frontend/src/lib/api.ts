export type SourceKind = "pdf" | "code" | "text";
export type MaterialKind = "lecture" | "code";
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
  material_kind: MaterialKind;
  size_bytes: number;
  created_at: string;
  status: RecordStatus;
  user_id: string;
  date_folder: string;
  relative_path: string;
  topic: string;
  note_id: string | null;
}

export interface FolderUploadResult {
  items: SourceItem[];
  classified_by: "gemini" | "heuristic" | "topic";
  message: string;
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

export interface DeskItem {
  kind: "note" | "source";
  id: string;
  title: string;
  href: string;
  preview: string | null;
}

export interface DeskSection {
  id: string;
  title: string;
  items: DeskItem[];
}

export interface DeskResponse {
  user_id: string;
  user_name: string;
  sections: DeskSection[];
  unfiled: DeskItem[];
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
  sources: (kind?: MaterialKind) => {
    const query = kind ? `?kind=${kind}` : "";
    return request<SourceItem[]>(`/api/sources${query}`);
  },
  notes: (userId: string) => request<NoteItem[]>(withUser("/api/notes", userId)),
  note: (id: string) => request<NoteItem>(`/api/notes/${id}`),
  jobs: (userId: string) => request<JobItem[]>(withUser("/api/jobs", userId)),
  createNote: (userId: string, title?: string) =>
    request<NoteItem>("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: title ?? "새 노트", user_id: userId }),
    }),
  uploadSource: async (
    userId: string,
    file: File,
    meta?: { topic?: string; studyDate?: string; materialKind?: MaterialKind },
  ) => {
    const data = new FormData();
    data.append("file", file);
    data.append("user_id", userId);
    if (meta?.topic) data.append("topic", meta.topic);
    if (meta?.studyDate) data.append("study_date", meta.studyDate);
    if (meta?.materialKind) data.append("material_kind", meta.materialKind);
    return request<SourceItem>("/api/sources", { method: "POST", body: data });
  },
  uploadCodeFolder: async (
    userId: string,
    files: File[],
    meta?: { topic?: string; studyDate?: string },
  ) => {
    const data = new FormData();
    data.append("user_id", userId);
    if (meta?.topic) data.append("topic", meta.topic);
    if (meta?.studyDate) data.append("study_date", meta.studyDate);
    for (const file of files) {
      const relative = file.webkitRelativePath || file.name;
      data.append("files", file, file.name);
      data.append("paths", relative);
    }
    return request<FolderUploadResult>("/api/sources/folder", { method: "POST", body: data });
  },
  desk: (userId: string) => request<DeskResponse>(withUser("/api/desk", userId)),
  createDeskSection: (userId: string, title: string) =>
    request<DeskResponse>("/api/desk/sections", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, title }),
    }),
  renameDeskSection: (userId: string, sectionId: string, title: string) =>
    request<DeskResponse>(`/api/desk/sections/${sectionId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, title }),
    }),
  deleteDeskSection: (userId: string, sectionId: string) =>
    request<DeskResponse>(withUser(`/api/desk/sections/${sectionId}`, userId), { method: "DELETE" }),
  moveDeskItem: (
    userId: string,
    kind: "note" | "source",
    itemId: string,
    sectionId: string | null,
  ) =>
    request<DeskResponse>("/api/desk/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, kind, item_id: itemId, section_id: sectionId }),
    }),
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
