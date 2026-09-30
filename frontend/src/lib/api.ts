export type SourceKind = "pdf" | "code" | "text";
export type RecordStatus = "uploaded" | "processing" | "ready" | "error" | "draft";
export type JobStatus = "queued" | "running" | "done" | "error";

export interface SourceItem {
  id: string;
  filename: string;
  source_type: SourceKind;
  size_bytes: number;
  created_at: string;
  status: RecordStatus;
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
}

export interface JobItem {
  id: string;
  kind: "upload" | "note";
  status: JobStatus;
  message: string;
  source_id: string | null;
  note_id: string | null;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  graph_available: boolean;
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

export const api = {
  health: () => request<HealthResponse>("/api/health"),
  sources: () => request<SourceItem[]>("/api/sources"),
  notes: () => request<NoteItem[]>("/api/notes"),
  note: (id: string) => request<NoteItem>(`/api/notes/${id}`),
  jobs: () => request<JobItem[]>("/api/jobs"),
  createNote: (title?: string) =>
    request<NoteItem>("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: title ?? "새 노트" }),
    }),
  uploadSource: async (file: File) => {
    const data = new FormData();
    data.append("file", file);
    return request<SourceItem>("/api/sources", { method: "POST", body: data });
  },
};
