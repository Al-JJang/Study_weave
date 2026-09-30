import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "@/App";
import { EmptyState } from "@/components/Status";
import { USER_STORAGE_KEY } from "@/lib/team";

function jsonOk(data: unknown) {
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve(data),
  });
}

const emptyDesk = {
  user_id: "seoyoung",
  user_name: "서영",
  sections: [] as { id: string; title: string; items: unknown[] }[],
  unfiled: [] as unknown[],
};

describe("StudyWeave UI", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/desk")) {
          const userId = new URL(url, "http://local.invalid").searchParams.get("user_id") ?? "seoyoung";
          const names: Record<string, string> = {
            seoyoung: "서영",
            songju: "송주",
            saegyeol: "새결",
            donggyu: "동규",
          };
          return jsonOk({ ...emptyDesk, user_id: userId, user_name: names[userId] ?? userId });
        }
        return jsonOk([]);
      }),
    );
  });

  it("대시보드에 제목·설명·사용자 선택과 카드가 보인다", async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getAllByText("StudyWeave AI").length).toBeGreaterThan(0);
    expect(screen.getAllByAltText("StudyWeave AI").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "StudyWeave AI" })).toBeInTheDocument();
    expect(
      screen.getByText("올린 수업 자료로 노트와 퀴즈를 만들고 검색합니다."),
    ).toBeInTheDocument();
    expect(screen.queryByText("안녕하세요")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "학습 도우미" })).not.toBeInTheDocument();
    expect(screen.getByRole("listbox", { name: "사용자 선택" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "동규" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "수업 내용 검색" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "소스 업로드" })).toBeInTheDocument();
    expect(await screen.findByText("아직 노트가 없습니다")).toBeInTheDocument();
  });

  it("사용자 선택은 개인 작업 공간으로 이동한다", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    await user.click(screen.getByRole("option", { name: "동규" }));
    expect(localStorage.getItem(USER_STORAGE_KEY)).toBe("donggyu");
    expect(await screen.findByRole("heading", { name: "동규의 작업 공간" })).toBeInTheDocument();
    expect(
      screen.queryByText("올린 수업 자료로 노트와 퀴즈를 만들고 검색합니다."),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "학습 도우미" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "섹션 추가" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "섹션 보기" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "탭" })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "접기" }));
    expect(screen.getByRole("button", { name: "접기" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: /아직 안 나눔/ })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("option", { name: "동규" })).toHaveAttribute("aria-selected", "true");
  });

  it("empty 상태 문구를 보여준다", () => {
    render(
      <EmptyState title="아직 소스가 없습니다" description="PDF나 코드 파일을 올리세요." />,
    );
    expect(screen.getByText("아직 소스가 없습니다")).toBeInTheDocument();
  });

  it("소스 탭에서 날짜와 주제로 분류한다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/sources")) {
          return jsonOk([
            {
              id: "src-1",
              filename: "agent.py",
              source_type: "code",
              size_bytes: 12,
              created_at: "2026-07-21T10:00:00+00:00",
              status: "ready",
              user_id: "seoyoung",
              date_folder: "2026-07-21",
              topic: "에이전트",
              relative_path: "seoyoung/2026-07-21/에이전트/agent.py",
              note_id: null,
            },
          ]);
        }
        return jsonOk([]);
      }),
    );
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/sources"]}>
        <App />
      </MemoryRouter>,
    );
    expect(await screen.findByText("agent.py")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /7월 21일/ })).toBeInTheDocument();
    expect(screen.getByText("에이전트")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "날짜별" })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "주제별" }));
    expect(screen.getByRole("heading", { name: "에이전트" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "7월" })).toBeInTheDocument();
  });
});
