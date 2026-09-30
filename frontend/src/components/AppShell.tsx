import { FileUp, LayoutDashboard, Menu, X } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useTeamUser, type TeamUserId } from "@/lib/team";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/", label: "대시보드", icon: LayoutDashboard, end: true },
  { to: "/sources", label: "소스", icon: FileUp, end: false },
];

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1">
      {nav.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium",
              isActive ? "bg-lavender-soft text-lavender" : "text-muted hover:bg-cream",
            )
          }
        >
          <item.icon className="h-4 w-4" />
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

function UserPicker({ onNavigate }: { onNavigate?: () => void }) {
  const { userId, users, setUserId } = useTeamUser();
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="mt-6">
      <p className="mb-2 px-2 text-xs font-medium tracking-wide text-muted uppercase">사용자 선택</p>
      <div className="flex flex-col gap-1" role="listbox" aria-label="사용자 선택">
        {users.map((user) => {
          const selected = user.id === userId && location.pathname.startsWith(`/u/${user.id}`);
          return (
            <button
              key={user.id}
              type="button"
              role="option"
              aria-selected={selected}
              onClick={() => {
                setUserId(user.id as TeamUserId);
                navigate(`/u/${user.id}`);
                onNavigate?.();
              }}
              className={cn(
                "rounded-2xl px-3 py-2.5 text-left text-sm font-medium",
                selected ? "bg-lavender-soft text-lavender" : "text-muted hover:bg-cream",
              )}
            >
              {user.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function AppShell() {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-svh bg-cream text-ink">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-[#efeaf6] bg-white px-4 py-5 md:flex">
        <Brand />
        <NavItems />
        <UserPicker />
        <UserChip />
      </aside>

      {open ? (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-ink/30"
            aria-label="메뉴 닫기"
            onClick={() => setOpen(false)}
          />
          <aside className="relative flex h-full w-72 flex-col bg-white px-4 py-5">
            <div className="mb-4 flex items-center justify-between">
              <Brand />
              <Button variant="ghost" size="icon" onClick={() => setOpen(false)} aria-label="닫기">
                <X className="h-5 w-5" />
              </Button>
            </div>
            <NavItems onNavigate={() => setOpen(false)} />
            <UserPicker onNavigate={() => setOpen(false)} />
            <UserChip />
          </aside>
        </div>
      ) : null}

      <div className="md:pl-64">
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-[#efeaf6] bg-cream/90 px-4 py-3 backdrop-blur md:hidden">
          <Button variant="ghost" size="icon" onClick={() => setOpen(true)} aria-label="메뉴 열기">
            <Menu className="h-5 w-5" />
          </Button>
          <BrandMark />
        </header>
        <main className="px-4 py-6 sm:px-8 lg:px-12">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function Brand() {
  return (
    <div className="mb-8 px-2">
      <BrandMark />
    </div>
  );
}

function BrandMark() {
  return (
    <div className="flex items-center gap-2">
      <img
        src="/studyweave-logo.png"
        alt="StudyWeave AI"
        className="h-9 w-9 shrink-0 rounded-xl object-cover object-[50%_28%]"
      />
      <span className="font-semibold tracking-tight">StudyWeave AI</span>
    </div>
  );
}

function UserChip() {
  const { user } = useTeamUser();
  return (
    <div className="mt-auto rounded-2xl bg-cream px-3 py-3 text-sm">
      <p className="font-medium">{user.name}</p>
      <p className="text-xs text-muted">팀 내부 학습 도구</p>
    </div>
  );
}
