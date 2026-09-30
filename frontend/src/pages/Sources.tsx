import { CalendarDays, FolderOpen, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import { EmptyState, ErrorState, LoadingState } from "@/components/Status";
import { UploadDialog } from "@/components/UploadDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useWorkspace } from "@/hooks/useWorkspace";
import { type SourceItem } from "@/lib/api";
import {
  formatStudyDay,
  groupByDate,
  groupByTopic,
  inMonth,
  matchesQuery,
  MATERIAL_KINDS,
  parseMaterialKind,
  STUDY_MONTHS,
  topicTone,
} from "@/lib/sourceBrowse";
import { cn, formatBytes } from "@/lib/utils";

const typeLabel = { pdf: "PDF", code: "코드", text: "텍스트" } as const;

export function SourcesPage() {
  const { kind: kindParam } = useParams();
  const kind = parseMaterialKind(kindParam === "lectures" ? "lecture" : kindParam);
  const copy = MATERIAL_KINDS[kind];
  const { sources, loading, error, refresh } = useWorkspace();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [month, setMonth] = useState<(typeof STUDY_MONTHS)[number]["id"]>("all");
  const [group, setGroup] = useState<"date" | "topic">("date");

  const library = useMemo(
    () => sources.filter((source) => source.material_kind === kind),
    [kind, sources],
  );

  const topics = useMemo(
    () => [...new Set(library.map((source) => source.topic).filter(Boolean))].sort((a, b) => a.localeCompare(b, "ko")),
    [library],
  );

  const visible = useMemo(() => {
    const prefix = STUDY_MONTHS.find((item) => item.id === month)?.prefix ?? "";
    return library.filter((source) => inMonth(source.date_folder, prefix) && matchesQuery(source, query));
  }, [library, month, query]);

  const dateGroups = useMemo(() => groupByDate(visible), [visible]);
  const topicGroups = useMemo(() => groupByTopic(visible), [visible]);

  if (kindParam !== "lectures" && kindParam !== "code") {
    return <Navigate to="/sources/lectures" replace />;
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{copy.label}</h1>
          <p className="mt-1 text-sm text-muted">
            강사님이 올려 주신 {copy.label}를 팀이 같이 봅니다. 7월부터 10월까지 날짜와 주제로 찾아보세요.
          </p>
        </div>
        <Button onClick={() => setUploadOpen(true)}>{copy.uploadLabel}</Button>
      </div>

      <div className="mt-6 rounded-[28px] border border-[#efeaf6] bg-white p-4 shadow-sm">
        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-4 h-4 w-4 -translate-y-1/2 text-muted" />
          <Input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="주제, 파일 이름, 날짜로 찾기"
            aria-label={copy.searchLabel}
            className="h-12 rounded-2xl pl-11"
          />
        </div>
        <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="월 필터">
            {STUDY_MONTHS.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={month === item.id}
                onClick={() => setMonth(item.id)}
                className={cn(
                  "rounded-full px-3 py-1.5 text-sm font-medium transition",
                  month === item.id ? "bg-lavender text-white" : "bg-cream text-muted hover:text-ink",
                )}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="inline-flex rounded-2xl bg-cream p-1" role="group" aria-label="분류 보기">
            <button
              type="button"
              aria-pressed={group === "date"}
              onClick={() => setGroup("date")}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-sm font-medium",
                group === "date" ? "bg-white text-lavender shadow-sm" : "text-muted",
              )}
            >
              <CalendarDays className="h-3.5 w-3.5" />
              날짜별
            </button>
            <button
              type="button"
              aria-pressed={group === "topic"}
              onClick={() => setGroup("topic")}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-sm font-medium",
                group === "topic" ? "bg-white text-lavender shadow-sm" : "text-muted",
              )}
            >
              <FolderOpen className="h-3.5 w-3.5" />
              주제별
            </button>
          </div>
        </div>
      </div>

      <div className="mt-6">
        {loading ? <LoadingState label={copy.loadingLabel} /> : null}
        {error ? (
          <ErrorState message={`${copy.label}를 불러오지 못했습니다. ${error}`} onRetry={() => void refresh()} />
        ) : null}
        {!loading && !error && library.length === 0 ? (
          <EmptyState
            title={copy.emptyTitle}
            description={copy.emptyDescription}
            action={<Button onClick={() => setUploadOpen(true)}>{copy.uploadLabel}</Button>}
          />
        ) : null}
        {!loading && !error && library.length > 0 && visible.length === 0 ? (
          <EmptyState title="검색 결과가 없습니다" description="다른 월이나 주제로 찾아보세요." />
        ) : null}
        {!loading && !error && visible.length > 0 && group === "date" ? (
          <div className="space-y-4">
            {dateGroups.map(([dateFolder, files]) => (
              <section key={dateFolder} className="overflow-hidden rounded-[28px] border border-[#efeaf6] bg-white shadow-sm">
                <div className="flex items-center justify-between border-b border-[#efeaf6] bg-[#faf8ff] px-5 py-3">
                  <h2 className="text-sm font-semibold">{formatStudyDay(dateFolder)}</h2>
                  <span className="text-xs text-muted">{files.length}개</span>
                </div>
                <ul className="grid gap-2 p-4">
                  {files.map((source) => (
                    <SourceRow key={source.id} source={source} />
                  ))}
                </ul>
              </section>
            ))}
          </div>
        ) : null}
        {!loading && !error && visible.length > 0 && group === "topic" ? (
          <div className="grid gap-4 md:grid-cols-2">
            {topicGroups.map(([topic, files]) => {
              const tone = topicTone(topic);
              return (
                <section key={topic} className="overflow-hidden rounded-[28px] border border-[#efeaf6] bg-white shadow-sm">
                  <div className={cn("flex items-center justify-between px-5 py-3", tone.bg)}>
                    <h2 className={cn("text-sm font-semibold", tone.text)}>{topic}</h2>
                    <span className={cn("text-xs", tone.text)}>{files.length}개</span>
                  </div>
                  <ul className="grid gap-2 p-4">
                    {files.map((source) => (
                      <SourceRow key={source.id} source={source} hideTopic />
                    ))}
                  </ul>
                </section>
              );
            })}
          </div>
        ) : null}
      </div>

      <UploadDialog
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        onUploaded={() => void refresh()}
        topics={topics}
        materialKind={kind}
      />
    </div>
  );
}

function SourceRow({ source, hideTopic }: { source: SourceItem; hideTopic?: boolean }) {
  const tone = topicTone(source.topic);
  return (
    <li className="flex flex-col gap-2 rounded-2xl bg-cream px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="font-medium">{source.filename}</p>
        <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted">
          {hideTopic ? null : (
            <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", tone.bg, tone.text)}>
              {source.topic}
            </span>
          )}
          <span>
            {typeLabel[source.source_type]} · {formatBytes(source.size_bytes)}
          </span>
          {hideTopic ? <span>{formatStudyDay(source.date_folder)}</span> : null}
        </p>
      </div>
      <StatusPill status={source.status} />
    </li>
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
