import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { EmptyState, ErrorState, LoadingState } from "@/components/Status";
import { Button } from "@/components/ui/button";
import { useWorkspace } from "@/hooks/useWorkspace";
import { api } from "@/lib/api";
import { formatWhen } from "@/lib/utils";

export function NotesPage() {
  const { notes, loading, error, refresh } = useWorkspace();
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  const createNote = async () => {
    setCreating(true);
    try {
      const note = await api.createNote("새 노트");
      navigate(`/notes/${note.id}`);
    } catch {
      await refresh();
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">강의 진행 기록</h1>
          <p className="mt-1 text-sm text-muted">소스에서 만든 학습 노트와 직접 만든 빈 노트입니다.</p>
        </div>
        <Button onClick={() => void createNote()} disabled={creating}>
          {creating ? "만드는 중…" : "새 노트 생성"}
        </Button>
      </div>

      <div className="mt-6">
        {loading ? <LoadingState label="노트를 불러오는 중" /> : null}
        {error ? (
          <ErrorState message={`노트를 불러오지 못했습니다. ${error}`} onRetry={() => void refresh()} />
        ) : null}
        {!loading && !error && notes.length === 0 ? (
          <EmptyState
            title="아직 노트가 없습니다"
            description="새 노트를 만들거나 소스를 업로드해 보세요."
            action={<Button onClick={() => void createNote()}>새 노트 생성</Button>}
          />
        ) : null}
        {!loading && !error && notes.length > 0 ? (
          <ul className="grid gap-3 md:grid-cols-2">
            {notes.map((note) => (
              <li key={note.id}>
                <Link
                  to={`/notes/${note.id}`}
                  className="block h-full rounded-3xl border border-[#efeaf6] bg-white p-5 hover:border-lavender/40"
                >
                  <p className="font-medium">{note.title}</p>
                  <p className="mt-2 line-clamp-3 text-sm text-muted">{note.preview}</p>
                  <p className="mt-3 text-xs text-muted">{formatWhen(note.created_at)}</p>
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}
