import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { EmptyState, ErrorState, LoadingState } from "@/components/Status";
import { api, type NoteItem } from "@/lib/api";
import { formatWhen } from "@/lib/utils";

export function NoteDetailPage() {
  const { noteId } = useParams();
  const [note, setNote] = useState<NoteItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!noteId) return;
    setLoading(true);
    setError(null);
    try {
      setNote(await api.note(noteId));
    } catch (err) {
      setNote(null);
      setError(err instanceof Error ? err.message : "노트를 열 수 없습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [noteId]);

  if (loading) return <LoadingState label="노트를 여는 중" />;
  if (error) {
    return (
      <ErrorState
        message={error === "노트를 찾을 수 없습니다." ? error : `노트를 열지 못했습니다. ${error}`}
        onRetry={() => void load()}
      />
    );
  }
  if (!note) {
    return (
      <EmptyState
        title="노트를 찾을 수 없습니다"
        description="목록으로 돌아가 다른 노트를 열어 보세요."
        action={
          <Link to="/notes" className="text-sm text-lavender hover:underline">
            노트 목록
          </Link>
        }
      />
    );
  }

  return (
    <article className="mx-auto max-w-3xl">
      <Link to="/notes" className="text-sm text-muted hover:text-lavender">
        ← 노트 목록
      </Link>
      <h1 className="mt-4 text-3xl font-semibold">{note.title}</h1>
      <p className="mt-2 text-sm text-muted">{formatWhen(note.created_at)}</p>
      <pre className="mt-8 overflow-x-auto whitespace-pre-wrap rounded-3xl bg-white p-6 text-sm leading-7 text-ink">
        {note.markdown}
      </pre>
    </article>
  );
}
