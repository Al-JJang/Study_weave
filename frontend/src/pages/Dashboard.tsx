import { FileStack, FileUp, NotebookPen, Search } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { EmptyState, ErrorState, LoadingState } from "@/components/Status";
import { UploadDialog } from "@/components/UploadDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useWorkspace } from "@/hooks/useWorkspace";
import { api } from "@/lib/api";
import { formatWhen } from "@/lib/utils";

export function DashboardPage() {
  const { notes, sources, loading, error, refresh } = useWorkspace();
  const [query, setQuery] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  const filteredNotes = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return notes;
    return notes.filter(
      (note) =>
        note.title.toLowerCase().includes(q) || note.preview.toLowerCase().includes(q),
    );
  }, [notes, query]);

  const createNote = async () => {
    setCreating(true);
    try {
      const note = await api.createNote("새 노트");
      await refresh();
      navigate(`/notes/${note.id}`);
    } catch {
      await refresh();
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl">
      <p className="text-lg text-muted">안녕하세요</p>
      <h1 className="mt-1 max-w-2xl bg-linear-to-r from-[#4f3ed4] to-[#9a7dff] bg-clip-text text-3xl font-semibold tracking-tight text-transparent sm:text-4xl">
        StudyWeave가 학습에 어떻게 도움이 될까요?
      </h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
        수업 자료와 코드를 올리면 개념 정리, 코드 흐름, 복습 퀴즈가 한 노트로 모입니다.
        팀원끼리만 쓰는 학습 도구라 계정이나 결제 없이 바로 쓰면 됩니다.
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <ActionCard
          title="소스 업로드"
          description="PDF, 코드, 텍스트에서 학습 노트를 만드세요."
          onClick={() => setUploadOpen(true)}
          illustration={<UploadArt />}
        />
        <ActionCard
          title="새 노트 생성"
          description="빈 노트를 만들고 나중에 소스를 연결하세요."
          onClick={() => void createNote()}
          disabled={creating}
          illustration={<NoteArt />}
        />
        <ActionCard
          title="학습 노트 열기"
          description="이미 만든 노트를 이어서 읽습니다."
          to="/notes"
          illustration={<StackArt />}
        />
      </div>

      <section className="mt-10">
        <h2 className="mb-3 text-base font-semibold">내 노트 파헤치기</h2>
        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-4 h-4 w-4 -translate-y-1/2 text-muted" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="최근 수업이나 코드에 대해 찾아보세요"
            className="h-14 rounded-3xl pl-11"
            aria-label="노트 검색"
          />
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-full border border-[#e4def3] bg-white px-3 py-1.5 text-xs text-muted hover:bg-lavender-soft"
            onClick={() => setQuery("노트")}
          >
            내 노트 요약하기
          </button>
          <button
            type="button"
            className="rounded-full border border-[#e4def3] bg-white px-3 py-1.5 text-xs text-muted hover:bg-lavender-soft"
            onClick={() => setQuery("개념")}
          >
            이 개념을 설명해 주세요
          </button>
          <button
            type="button"
            className="rounded-full border border-[#e4def3] bg-white px-3 py-1.5 text-xs text-muted hover:bg-lavender-soft"
            onClick={() => navigate("/sources")}
          >
            관련 자료 찾기
          </button>
        </div>
      </section>

      <section className="mt-10">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold">최근 노트</h2>
          <span className="text-xs text-muted">소스 {sources.length}개 · 노트 {notes.length}개</span>
        </div>
        {loading ? <LoadingState label="노트를 불러오는 중" /> : null}
        {error ? <ErrorState message={`목록을 불러오지 못했습니다. ${error}`} onRetry={() => void refresh()} /> : null}
        {!loading && !error && filteredNotes.length === 0 ? (
          <EmptyState
            title={query ? "검색 결과가 없습니다" : "아직 노트가 없습니다"}
            description={
              query
                ? "다른 단어로 검색하거나 새 노트를 만들어 보세요."
                : "소스를 올리거나 빈 노트를 만들면 여기에 나타납니다."
            }
            action={
              <Button onClick={() => setUploadOpen(true)}>
                <FileUp className="h-4 w-4" />
                소스 업로드
              </Button>
            }
          />
        ) : null}
        {!loading && !error && filteredNotes.length > 0 ? (
          <ul className="grid gap-3">
            {filteredNotes.slice(0, 5).map((note) => (
              <li key={note.id}>
                <Link
                  to={`/notes/${note.id}`}
                  className="block rounded-3xl border border-[#efeaf6] bg-white p-5 hover:border-lavender/40"
                >
                  <p className="font-medium">{note.title}</p>
                  <p className="mt-1 line-clamp-2 text-sm text-muted">{note.preview}</p>
                  <p className="mt-2 text-xs text-muted">{formatWhen(note.created_at)}</p>
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <UploadDialog
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        onUploaded={(source) => {
          void refresh();
          if (source.note_id) navigate(`/notes/${source.note_id}`);
        }}
      />
    </div>
  );
}

function ActionCard({
  title,
  description,
  illustration,
  onClick,
  to,
  disabled,
}: {
  title: string;
  description: string;
  illustration: ReactNode;
  onClick?: () => void;
  to?: string;
  disabled?: boolean;
}) {
  const inner = (
    <>
      <div>
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="mt-1 text-sm text-muted">{description}</p>
      </div>
      <div className="mt-6 h-28 overflow-hidden rounded-2xl">{illustration}</div>
    </>
  );
  const className =
    "flex h-full flex-col justify-between rounded-3xl border border-[#efeaf6] bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md disabled:opacity-60";

  if (to) {
    return (
      <Link to={to} className={className}>
        {inner}
      </Link>
    );
  }
  return (
    <button type="button" className={className} onClick={onClick} disabled={disabled}>
      {inner}
    </button>
  );
}

function UploadArt() {
  return (
    <div className="dot-grid flex h-full items-end justify-center bg-[#f3edff] p-4">
      <FileUp className="h-16 w-16 text-lavender" />
    </div>
  );
}

function NoteArt() {
  return (
    <div className="dot-grid flex h-full items-end justify-center bg-[#fff4e8] p-4">
      <NotebookPen className="h-16 w-16 text-[#e08a3a]" />
    </div>
  );
}

function StackArt() {
  return (
    <div className="dot-grid flex h-full items-end justify-center bg-[#eef6ff] p-4">
      <FileStack className="h-16 w-16 text-[#4b7fd6]" />
    </div>
  );
}
