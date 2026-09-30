import { useEffect, useState } from "react";
import { api, type NoteItem, type SourceItem } from "@/lib/api";

interface WorkspaceData {
  notes: NoteItem[];
  sources: SourceItem[];
}

export function useWorkspace() {
  const [data, setData] = useState<WorkspaceData>({ notes: [], sources: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const [notes, sources] = await Promise.all([api.notes(), api.sources()]);
      setData({ notes, sources });
    } catch (err) {
      setError(err instanceof Error ? err.message : "서버에 연결하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  return { ...data, loading, error, refresh };
}
