import { ChevronDown, FolderOpen, LayoutList, Rows3 } from "lucide-react";
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { DashboardChat } from "@/components/DashboardChat";
import { ErrorState, LoadingState } from "@/components/Status";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, type DeskItem, type DeskResponse, type DeskSection } from "@/lib/api";
import { isTeamUserId, useTeamUser, type TeamUserId } from "@/lib/team";
import { cn } from "@/lib/utils";

const UNFILED_ID = "unfiled";
export const DESK_VIEW_KEY = "studyweave-desk-view";
type DeskView = "tabs" | "accordion";

function readView(): DeskView {
  try {
    const saved = localStorage.getItem(DESK_VIEW_KEY);
    if (saved === "tabs" || saved === "accordion") return saved;
  } catch {
    /* ignore */
  }
  return "tabs";
}

export function DeskPage() {
  const { userId: routeUserId } = useParams();
  const { setUserId, user } = useTeamUser();
  const [desk, setDesk] = useState<DeskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [view, setViewState] = useState<DeskView>(readView);
  const [activeId, setActiveId] = useState(UNFILED_ID);
  const [openIds, setOpenIds] = useState<string[]>([UNFILED_ID]);

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

  const panes = useMemo(() => {
    if (!desk) return [];
    return [
      {
        id: UNFILED_ID,
        title: "아직 안 나눔",
        description: "섹션에 넣지 않은 노트와 업로드입니다.",
        items: desk.unfiled,
        emptyTitle: "아직 넣을 자료가 없습니다",
        emptyDescription: "대시보드에서 소스를 올리거나 노트를 만들면 여기에 나타납니다.",
      },
      ...desk.sections.map((section) => ({
        id: section.id,
        title: section.title,
        description: undefined as string | undefined,
        items: section.items,
        section,
        emptyTitle: "이 섹션은 비어 있습니다",
        emptyDescription: "자료를 이 섹션으로 옮기세요.",
      })),
    ];
  }, [desk]);

  useEffect(() => {
    const ids = new Set(panes.map((pane) => pane.id));
    if (panes.length > 0 && !ids.has(activeId)) setActiveId(UNFILED_ID);
    setOpenIds((current) => {
      const next = current.filter((id) => ids.has(id));
      if (next.length === 0) return [UNFILED_ID];
      if (next.length === current.length && next.every((id, index) => id === current[index])) {
        return current;
      }
      return next;
    });
  }, [activeId, panes]);

  if (!valid || !routeUserId) {
    return <Navigate to="/" replace />;
  }

  const setView = (next: DeskView) => {
    setViewState(next);
    try {
      localStorage.setItem(DESK_VIEW_KEY, next);
    } catch {
      /* ignore */
    }
  };

  const addSection = async (event: FormEvent) => {
    event.preventDefault();
    const title = newTitle.trim();
    if (!title || creating) return;
    setCreating(true);
    try {
      const next = await api.createDeskSection(routeUserId, title);
      setDesk(next);
      setNewTitle("");
      const created = next.sections.at(-1);
      if (created) {
        setActiveId(created.id);
        setOpenIds((current) => (current.includes(created.id) ? current : [...current, created.id]));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "섹션을 만들지 못했습니다.");
    } finally {
      setCreating(false);
    }
  };

  const applyDesk = (next: DeskResponse) => setDesk(next);
  const active = panes.find((pane) => pane.id === activeId) ?? panes[0];

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="text-2xl font-semibold">{user.name}의 작업 공간</h1>
      <p className="mt-1 text-sm text-muted">섹션을 탭이나 접기로 보고, 노트와 업로드를 나눠 두세요.</p>

      <div className="mt-6 rounded-[28px] border border-[#efeaf6] bg-white p-4 shadow-sm sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <ViewSwitch view={view} onChange={setView} />
          <form className="flex flex-1 gap-2 lg:max-w-md" onSubmit={(event) => void addSection(event)}>
            <Input
              value={newTitle}
              onChange={(event) => setNewTitle(event.target.value)}
              placeholder="새 섹션 이름"
              aria-label="새 섹션 이름"
              className="h-10"
            />
            <Button type="submit" disabled={creating || !newTitle.trim()}>
              {creating ? "만드는 중…" : "섹션 추가"}
            </Button>
          </form>
        </div>
      </div>

      {loading ? (
        <div className="mt-6">
          <LoadingState label="작업 공간을 불러오는 중" />
        </div>
      ) : null}
      {error ? (
        <div className="mt-6">
          <ErrorState message={error} onRetry={() => void refresh(routeUserId)} />
        </div>
      ) : null}

      {!loading && desk && active ? (
        <div className="mt-6">
          {view === "tabs" ? (
            <TabsBoard
              panes={panes}
              activeId={active.id}
              onSelect={setActiveId}
              desk={desk}
              userId={routeUserId}
              onChange={applyDesk}
            />
          ) : (
            <AccordionBoard
              panes={panes}
              openIds={openIds}
              onToggle={(id) =>
                setOpenIds((current) =>
                  current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
                )
              }
              desk={desk}
              userId={routeUserId}
              onChange={applyDesk}
            />
          )}
        </div>
      ) : null}

      <div className="mt-10">
        <DashboardChat key={routeUserId} />
      </div>
    </div>
  );
}

function ViewSwitch({ view, onChange }: { view: DeskView; onChange: (view: DeskView) => void }) {
  return (
    <div className="inline-flex rounded-2xl bg-cream p-1" role="group" aria-label="섹션 보기">
      <ViewButton
        pressed={view === "tabs"}
        icon={<LayoutList className="h-4 w-4" />}
        label="탭"
        onClick={() => onChange("tabs")}
      />
      <ViewButton
        pressed={view === "accordion"}
        icon={<Rows3 className="h-4 w-4" />}
        label="접기"
        onClick={() => onChange("accordion")}
      />
    </div>
  );
}

function ViewButton({
  pressed,
  icon,
  label,
  onClick,
}: {
  pressed: boolean;
  icon: ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-medium transition",
        pressed ? "bg-white text-lavender shadow-sm" : "text-muted hover:text-ink",
      )}
    >
      {icon}
      {label}
    </button>
  );
}

type Pane = {
  id: string;
  title: string;
  description?: string;
  items: DeskItem[];
  section?: DeskSection;
  emptyTitle: string;
  emptyDescription: string;
};

function TabsBoard({
  panes,
  activeId,
  onSelect,
  desk,
  userId,
  onChange,
}: {
  panes: Pane[];
  activeId: string;
  onSelect: (id: string) => void;
  desk: DeskResponse;
  userId: string;
  onChange: (desk: DeskResponse) => void;
}) {
  const active = panes.find((pane) => pane.id === activeId) ?? panes[0];
  return (
    <div className="overflow-hidden rounded-[28px] border border-[#efeaf6] bg-white shadow-sm">
      <div
        className="flex gap-1 overflow-x-auto border-b border-[#efeaf6] bg-[#faf8ff] px-3 py-3"
        role="tablist"
        aria-label="섹션"
      >
        {panes.map((pane) => {
          const selected = pane.id === active.id;
          return (
            <button
              key={pane.id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => onSelect(pane.id)}
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-2xl px-3.5 py-2 text-sm font-medium transition",
                selected ? "bg-lavender text-white shadow-sm" : "text-muted hover:bg-white hover:text-ink",
              )}
            >
              {pane.id === UNFILED_ID ? <FolderOpen className="h-3.5 w-3.5" /> : null}
              {pane.title}
              <span
                className={cn(
                  "rounded-full px-1.5 py-0.5 text-[11px] tabular-nums",
                  selected ? "bg-white/20 text-white" : "bg-lavender-soft text-lavender",
                )}
              >
                {pane.items.length}
              </span>
            </button>
          );
        })}
      </div>
      {active ? <PaneBody pane={active} desk={desk} userId={userId} onChange={onChange} /> : null}
    </div>
  );
}

function AccordionBoard({
  panes,
  openIds,
  onToggle,
  desk,
  userId,
  onChange,
}: {
  panes: Pane[];
  openIds: string[];
  onToggle: (id: string) => void;
  desk: DeskResponse;
  userId: string;
  onChange: (desk: DeskResponse) => void;
}) {
  return (
    <div className="space-y-3">
      {panes.map((pane) => {
        const open = openIds.includes(pane.id);
        return (
          <div key={pane.id} className="overflow-hidden rounded-[28px] border border-[#efeaf6] bg-white shadow-sm">
            <button
              type="button"
              aria-expanded={open}
              onClick={() => onToggle(pane.id)}
              className="flex w-full items-center gap-3 px-5 py-4 text-left"
            >
              <span
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-2xl",
                  open ? "bg-lavender-soft text-lavender" : "bg-cream text-muted",
                )}
              >
                <ChevronDown className={cn("h-4 w-4 transition", open ? "rotate-0" : "-rotate-90")} />
              </span>
              <span className="flex-1">
                <span className="block text-sm font-semibold">{pane.title}</span>
                {pane.description ? <span className="mt-0.5 block text-xs text-muted">{pane.description}</span> : null}
              </span>
              <span className="rounded-full bg-lavender-soft px-2 py-0.5 text-[11px] font-medium text-lavender tabular-nums">
                {pane.items.length}
              </span>
            </button>
            {open ? <PaneBody pane={pane} desk={desk} userId={userId} onChange={onChange} /> : null}
          </div>
        );
      })}
    </div>
  );
}

function PaneBody({
  pane,
  desk,
  userId,
  onChange,
}: {
  pane: Pane;
  desk: DeskResponse;
  userId: string;
  onChange: (desk: DeskResponse) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(pane.title);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setDraft(pane.title);
    setEditing(false);
  }, [pane.id, pane.title]);

  const rename = async () => {
    if (!pane.section) return;
    const next = draft.trim();
    if (!next) return;
    setBusy(true);
    try {
      onChange(await api.renameDeskSection(userId, pane.section.id, next));
      setEditing(false);
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!pane.section) return;
    setBusy(true);
    try {
      onChange(await api.deleteDeskSection(userId, pane.section.id));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="border-t border-[#efeaf6] px-5 py-5">
      {pane.section ? (
        <div className="mb-4 flex flex-wrap items-center justify-end gap-2">
          {editing ? (
            <form
              className="flex w-full flex-1 gap-2 sm:w-auto"
              onSubmit={(event) => {
                event.preventDefault();
                void rename();
              }}
            >
              <Input
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                aria-label="섹션 이름"
                className="h-9"
              />
              <Button type="submit" size="sm" disabled={busy}>
                저장
              </Button>
              <Button type="button" size="sm" variant="ghost" onClick={() => setEditing(false)}>
                취소
              </Button>
            </form>
          ) : (
            <>
              <Button type="button" size="sm" variant="outline" onClick={() => setEditing(true)}>
                이름 변경
              </Button>
              <Button type="button" size="sm" variant="ghost" disabled={busy} onClick={() => void remove()}>
                삭제
              </Button>
            </>
          )}
        </div>
      ) : pane.description ? (
        <p className="mb-4 text-xs text-muted">{pane.description}</p>
      ) : null}

      {pane.items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#e4def3] bg-cream/70 px-4 py-8 text-center">
          <p className="text-sm font-medium">{pane.emptyTitle}</p>
          <p className="mt-1 text-xs text-muted">{pane.emptyDescription}</p>
        </div>
      ) : (
        <ul className="grid gap-2">
          {pane.items.map((item) => (
            <li
              key={`${item.kind}-${item.id}`}
              className="flex flex-col gap-2 rounded-2xl bg-cream px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <Link to={item.href} className="font-medium hover:text-lavender">
                  {item.kind === "note" ? "노트" : "소스"} · {item.title}
                </Link>
                {item.preview ? <p className="mt-1 line-clamp-2 text-xs text-muted">{item.preview}</p> : null}
              </div>
              <label className="flex items-center gap-2 text-xs text-muted">
                옮기기
                <select
                  className="rounded-xl border border-[#e4def3] bg-white px-2 py-1.5 text-sm text-ink"
                  aria-label={`${item.title} 섹션으로 옮기기`}
                  value={pane.section?.id ?? ""}
                  onChange={(event) => {
                    const value = event.target.value;
                    void api
                      .moveDeskItem(userId, item.kind, item.id, value === "" ? null : value)
                      .then(onChange);
                  }}
                >
                  <option value="">아직 안 나눔</option>
                  {desk.sections.map((option) => (
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
    </div>
  );
}
