import { useCallback, useEffect, useState } from "react";
import { api, type NoteItem, type SourceItem } from "@/lib/api";
import { useTeamUser } from "@/lib/team";

interface WorkspaceData {
  notes: NoteItem[];
  sources: SourceItem[];
}

export function useWorkspace() {
  const { userId } = useTeamUser();
  const [data, setData] = useState<WorkspaceData>({ notes: [], sources: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [notes, sources] = await Promise.all([api.notes(userId), api.sources(userId)]);
      setData({ notes, sources });
    } catch (err) {
      setError(err instanceof Error ? err.message : "서버에 연결하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { ...data, loading, error, refresh, userId };
}
