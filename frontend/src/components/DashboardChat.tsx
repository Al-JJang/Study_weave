import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, type ChatTurn } from "@/lib/api";
import { useTeamUser } from "@/lib/team";

export function DashboardChat() {
  const { user, userId } = useTeamUser();
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const message = draft.trim();
    if (!message || busy) return;
    setDraft("");
    setError(null);
    setBusy(true);
    const prior = history;
    const nextHistory: ChatTurn[] = [...prior, { role: "user", content: message }];
    setHistory([...nextHistory, { role: "assistant", content: "" }]);
    try {
      const reply = await api.chat(userId, message, prior, (text) => {
        setHistory([...nextHistory, { role: "assistant", content: text }]);
      });
      setHistory([...nextHistory, { role: "assistant", content: reply || "응답이 비어 있습니다." }]);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "챗봇에 연결하지 못했습니다.";
      setError(detail);
      setHistory(prior);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="flex min-h-80 flex-col rounded-3xl border border-[#efeaf6] bg-white p-5">
      <h2 className="text-base font-semibold">학습 도우미</h2>
      <p className="mt-1 text-xs text-muted">{user.name}의 최근 노트를 바탕으로 질문합니다.</p>
      <div className="mt-4 flex min-h-48 flex-1 flex-col gap-2 overflow-y-auto pr-1">
        {history.length === 0 ? (
          <p className="text-sm text-muted">예: 이 노트에서 퀴즈 낼 개념만 골라 줘.</p>
        ) : null}
        {history.map((turn, index) => (
          <p
            key={`${turn.role}-${index}`}
            className={
              turn.role === "user"
                ? "self-end rounded-2xl bg-lavender-soft px-3 py-2 text-sm text-ink"
                : "rounded-2xl bg-cream px-3 py-2 text-sm whitespace-pre-wrap text-ink"
            }
          >
            {turn.content || (busy ? "답하는 중…" : "")}
          </p>
        ))}
      </div>
      {error ? (
        <p role="alert" className="mt-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}
      <form className="mt-4 flex gap-2" onSubmit={(event) => void submit(event)}>
        <Input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="노트 내용에 대해 묻기"
          aria-label="챗봇 질문"
          disabled={busy}
        />
        <Button type="submit" disabled={busy || !draft.trim()}>
          {busy ? "보내는 중" : "보내기"}
        </Button>
      </form>
    </section>
  );
}
