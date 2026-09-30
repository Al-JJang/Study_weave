import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

export const TEAM_USERS = [
  { id: "seoyoung", name: "서영" },
  { id: "songju", name: "송주" },
  { id: "saegyeol", name: "새결" },
  { id: "donggyu", name: "동규" },
] as const;

export type TeamUserId = (typeof TEAM_USERS)[number]["id"];
export type TeamUser = (typeof TEAM_USERS)[number];

export const DEFAULT_USER_ID: TeamUserId = "seoyoung";
export const USER_STORAGE_KEY = "studyweave-user-id";

function isTeamUserId(value: string | null): value is TeamUserId {
  return TEAM_USERS.some((user) => user.id === value);
}

function readStoredUserId(): TeamUserId {
  try {
    const saved = localStorage.getItem(USER_STORAGE_KEY);
    if (isTeamUserId(saved)) return saved;
  } catch {
    /* ignore */
  }
  return DEFAULT_USER_ID;
}

interface TeamUserContextValue {
  userId: TeamUserId;
  user: TeamUser;
  users: typeof TEAM_USERS;
  setUserId: (id: TeamUserId) => void;
}

const TeamUserContext = createContext<TeamUserContextValue | null>(null);

export function TeamUserProvider({ children }: { children: ReactNode }) {
  const [userId, setUserIdState] = useState<TeamUserId>(readStoredUserId);

  const value = useMemo<TeamUserContextValue>(() => {
    const user = TEAM_USERS.find((item) => item.id === userId) ?? TEAM_USERS[0];
    return {
      userId: user.id,
      user,
      users: TEAM_USERS,
      setUserId: (id: TeamUserId) => {
        setUserIdState(id);
        try {
          localStorage.setItem(USER_STORAGE_KEY, id);
        } catch {
          /* ignore */
        }
      },
    };
  }, [userId]);

  return <TeamUserContext.Provider value={value}>{children}</TeamUserContext.Provider>;
}

export function useTeamUser() {
  const context = useContext(TeamUserContext);
  if (!context) {
    throw new Error("useTeamUser는 TeamUserProvider 안에서만 쓸 수 있습니다.");
  }
  return context;
}
