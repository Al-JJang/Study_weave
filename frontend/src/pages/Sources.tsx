import { Folder } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState, ErrorState, LoadingState } from "@/components/Status";
import { UploadDialog } from "@/components/UploadDialog";
import { Button } from "@/components/ui/button";
import { useWorkspace } from "@/hooks/useWorkspace";
import { useTeamUser } from "@/lib/team";
import { formatBytes, formatWhen } from "@/lib/utils";

const typeLabel = { pdf: "PDF", code: "코드", text: "텍스트" } as const;

export function SourcesPage() {
  const { sources, loading, error, refresh } = useWorkspace();
  const { userId } = useTeamUser();
  const [uploadOpen, setUploadOpen] = useState(false);

  const grouped = useMemo(() => {
    const map = new Map<string, typeof sources>();
    for (const source of sources) {
      const key = source.date_folder || "날짜 없음";
      const items = map.get(key) ?? [];
      items.push(source);
      map.set(key, items);
    }
    return [...map.entries()].sort((left, right) => right[0].localeCompare(left[0]));
  }, [sources]);

  return (
    <div className="mx-auto max-w-5xl">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">소스</h1>
          <p className="mt-1 text-sm text-muted">
            {userId} 폴더에 날짜별로 모은 수업 자료입니다.
          </p>
        </div>
        <Button onClick={() => setUploadOpen(true)}>소스 업로드</Button>
      </div>

      <div className="mt-6">
        {loading ? <LoadingState label="소스를 불러오는 중" /> : null}
        {error ? (
          <ErrorState message={`소스를 불러오지 못했습니다. ${error}`} onRetry={() => void refresh()} />
        ) : null}
        {!loading && !error && sources.length === 0 ? (
          <EmptyState
            title="아직 소스가 없습니다"
            description="PDF나 코드 파일을 올리면 학습 노트 초안이 만들어집니다."
            action={<Button onClick={() => setUploadOpen(true)}>첫 소스 올리기</Button>}
          />
        ) : null}
        {!loading && !error && grouped.length > 0 ? (
          <div className="space-y-5">
            {grouped.map(([dateFolder, files]) => (
              <section key={dateFolder} className="rounded-3xl border border-[#efeaf6] bg-white p-5">
                <h2 className="flex items-center gap-2 text-sm font-semibold">
                  <Folder className="h-4 w-4 text-lavender" />
                  {userId}/{dateFolder}
                </h2>
                <ul className="mt-3 grid gap-3">
                  {files.map((source) => (
                    <li
                      key={source.id}
                      className="flex flex-col gap-2 rounded-2xl bg-cream px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <p className="font-medium">{source.filename}</p>
                        <p className="mt-1 text-sm text-muted">
                          {typeLabel[source.source_type]} · {formatBytes(source.size_bytes)} ·{" "}
                          {formatWhen(source.created_at)}
                        </p>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <StatusPill status={source.status} />
                        {source.note_id ? (
                          <Link to={`/notes/${source.note_id}`} className="text-lavender hover:underline">
                            노트 보기
                          </Link>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        ) : null}
      </div>

      <UploadDialog open={uploadOpen} onOpenChange={setUploadOpen} onUploaded={() => void refresh()} />
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const labels: Record<string, string> = {
    ready: "준비됨",
    processing: "처리 중",
    uploaded: "업로드됨",
    error: "오류",
    draft: "초안",
  };
  return (
    <span className="rounded-full bg-lavender-soft px-2.5 py-1 text-xs text-lavender">
      {labels[status] ?? status}
    </span>
  );
}
