import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "@/App";
import { EmptyState } from "@/components/Status";

describe("StudyWeave UI", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        }),
      ),
    );
  });

  it("대시보드에 한국어 인사와 카드가 보인다", async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getAllByText("StudyWeave AI").length).toBeGreaterThan(0);
    expect(screen.getAllByAltText("StudyWeave AI").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "강의 진행 기록" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "수업 내용 검색" })).toBeInTheDocument();
    expect(screen.getByRole("searchbox", { name: "수업 내용 검색" })).toBeInTheDocument();
    expect(screen.getByText("안녕하세요")).toBeInTheDocument();
    expect(
      await screen.findByText("StudyWeave가 학습에 어떻게 도움이 될까요?"),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "소스 업로드" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "새 노트 생성" })).toBeInTheDocument();
    expect(await screen.findByText("아직 노트가 없습니다")).toBeInTheDocument();
  });

  it("empty 상태 문구를 보여준다", () => {
    render(
      <EmptyState title="아직 소스가 없습니다" description="PDF나 코드 파일을 올리세요." />,
    );
    expect(screen.getByText("아직 소스가 없습니다")).toBeInTheDocument();
  });
});
