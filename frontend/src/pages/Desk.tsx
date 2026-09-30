import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { DashboardChat } from "@/components/DashboardChat";
import { EmptyState, ErrorState, LoadingState } from "@/components/Status";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, type DeskItem, type DeskResponse, type DeskSection } from "@/lib/api";
import { isTeamUserId, useTeamUser, type TeamUserId } from "@/lib/team";

export function DeskPage() {
  const { userId: routeUserId } = useParams();
  const { setUserId, user } = useTeamUser();
  const [desk, setDesk] = useState<DeskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [creating, setCreating] = useState(false);

  const valid = isTeamUserId(routeUserId ?? null);

  useEffect(() => {
    if (valid) setUserId(routeUserId as TeamUserId);
  }, [routeUserId, setUserId, valid]);

  const refresh = async (uid: string) => {
    setLoading(true);
    setError(null);
    try {
      setDesk(await api.desk(uid));
    } catch (err) {
      setDesk(null);
      setError(err instanceof Error ? err.message : "작업 공간을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (valid && routeUserId) void refresh(routeUserId);
  }, [routeUserId, valid]);

  if (!valid || !routeUserId) {
    return <Navigate to="/" replace />;
  }

  const addSection = async (event: FormEvent) => {
    event.preventDefault();
    const title = newTitle.trim();
    if (!title || creating) return;
    setCreating(true);
    try {
      setDesk(await api.createDeskSection(routeUserId, title));
      setNewTitle("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "섹션을 만들지 못했습니다.");
    } finally {
      setCreating(false);
    }
  };

  const applyDesk = (next: DeskResponse) => setDesk(next);

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="text-2xl font-semibold">{user.name}의 작업 공간</h1>
      <p className="mt-1 text-sm text-muted">
        섹션을 만들고 노트와 업로드를 나눠 두세요. 공용 대시보드와는 별도입니다.
      </p>

      <form className="mt-6 flex flex-col gap-2 sm:flex-row" onSubmit={(event) => void addSection(event)}>
        <Input
          value={newTitle}
          onChange={(event) => setNewTitle(event.target.value)}
          placeholder="새 섹션 이름"
          aria-label="새 섹션 이름"
        />
        <Button type="submit" disabled={creating || !newTitle.trim()}>
          {creating ? "만드는 중…" : "섹션 추가"}
        </Button>
      </form>

      {loading ? <div className="mt-6"><LoadingState label="작업 공간을 불러오는 중" /></div> : null}
      {error ? (
        <div className="mt-6">
          <ErrorState message={error} onRetry={() => void refresh(routeUserId)} />
        </div>
      ) : null}

      {!loading && desk ? (
        <div className="mt-8 space-y-6">
          <SectionBlock
            title="아직 안 나눔"
            description="섹션에 넣지 않은 노트와 업로드입니다."
            items={desk.unfiled}
            sections={desk.sections}
            userId={routeUserId}
            onChange={applyDesk}
            emptyTitle="아직 넣을 자료가 없습니다"
            emptyDescription="대시보드에서 소스를 올리거나 노트를 만들면 여기에 나타납니다."
          />
          {desk.sections.map((section) => (
            <SectionBlock
              key={section.id}
              title={section.title}
              items={section.items}
              sections={desk.sections}
              section={section}
              userId={routeUserId}
              onChange={applyDesk}
              emptyTitle="이 섹션은 비어 있습니다"
              emptyDescription="아래에서 자료를 이 섹션으로 옮기세요."
            />
          ))}
        </div>
      ) : null}

      <div className="mt-10">
        <DashboardChat key={routeUserId} />
      </div>
    </div>
  );
}

function SectionBlock({
  title,
  description,
  items,
  sections,
  section,
  userId,
  onChange,
  emptyTitle,
  emptyDescription,
}: {
  title: string;
  description?: string;
  items: DeskItem[];
  sections: DeskSection[];
  section?: DeskSection;
  userId: string;
  onChange: (desk: DeskResponse) => void;
  emptyTitle: string;
  emptyDescription: string;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(title);
  const [busy, setBusy] = useState(false);

  const rename = async () => {
    if (!section) return;
    const next = draft.trim();
    if (!next) return;
    setBusy(true);
    try {
      onChange(await api.renameDeskSection(userId, section.id, next));
      setEditing(false);
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!section) return;
    setBusy(true);
    try {
      onChange(await api.deleteDeskSection(userId, section.id));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="rounded-3xl border border-[#efeaf6] bg-white p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        {editing && section ? (
          <form
            className="flex flex-1 gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              void rename();
            }}
          >
            <Input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              aria-label="섹션 이름"
            />
            <Button type="submit" size="sm" disabled={busy}>
              저장
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => setEditing(false)}>
              취소
            </Button>
          </form>
        ) : (
          <div>
            <h2 className="text-base font-semibold">{title}</h2>
            {description ? <p className="mt-1 text-xs text-muted">{description}</p> : null}
          </div>
        )}
        {section && !editing ? (
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                setDraft(section.title);
                setEditing(true);
              }}
            >
              이름 변경
            </Button>
            <Button type="button" size="sm" variant="ghost" disabled={busy} onClick={() => void remove()}>
              삭제
            </Button>
          </div>
        ) : null}
      </div>
      {items.length === 0 ? (
        <div className="mt-4">
          <EmptyState title={emptyTitle} description={emptyDescription} />
        </div>
      ) : (
        <ul className="mt-4 grid gap-2">
          {items.map((item) => (
            <li
              key={`${item.kind}-${item.id}`}
              className="flex flex-col gap-2 rounded-2xl bg-cream px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <Link to={item.href} className="font-medium hover:text-lavender">
                  {item.kind === "note" ? "노트" : "소스"} · {item.title}
                </Link>
                {item.preview ? <p className="mt-1 text-xs text-muted">{item.preview}</p> : null}
              </div>
              <label className="flex items-center gap-2 text-xs text-muted">
                섹션으로 옮기기
                <select
                  className="rounded-xl border border-[#e4def3] bg-white px-2 py-1 text-sm text-ink"
                  aria-label={`${item.title} 섹션으로 옮기기`}
                  value={section?.id ?? ""}
                  onChange={(event) => {
                    const value = event.target.value;
                    void api
                      .moveDeskItem(userId, item.kind, item.id, value === "" ? null : value)
                      .then(onChange);
                  }}
                >
                  <option value="">아직 안 나눔</option>
                  {sections.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.title}
                    </option>
                  ))}
                </select>
              </label>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
