import { useState, type FormEvent } from "react";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, type SourceItem } from "@/lib/api";
import { useTeamUser } from "@/lib/team";

export function UploadDialog({
  open,
  onOpenChange,
  onUploaded,
  topics = [],
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUploaded: (source: SourceItem) => void;
  topics?: string[];
}) {
  const { userId } = useTeamUser();
  const [file, setFile] = useState<File | null>(null);
  const [topic, setTopic] = useState("");
  const [studyDate, setStudyDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError("파일을 선택하세요.");
      return;
    }
    if (!topic.trim()) {
      setError("그날 공부한 주제를 넣어 주세요.");
      return;
    }
    if (!studyDate.trim()) {
      setError("수업 날짜를 넣어 주세요.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const source = await api.uploadSource(userId, file, {
        topic: topic.trim(),
        studyDate: studyDate.trim(),
      });
      setFile(null);
      setTopic("");
      setStudyDate("");
      onOpenChange(false);
      onUploaded(source);
    } catch (err) {
      setError(err instanceof Error ? err.message : "업로드에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogTitle>소스 업로드</DialogTitle>
        <DialogDescription>
          날짜와 주제를 넣으면 7/21–9/30 일정에 맞춰 자동으로 분류됩니다.
        </DialogDescription>
        <form className="mt-5 space-y-4" onSubmit={(event) => void submit(event)}>
          <label className="block text-sm font-medium">
            수업 날짜
            <Input
              type="date"
              min="2026-07-21"
              max="2026-09-30"
              value={studyDate}
              onChange={(event) => setStudyDate(event.target.value)}
              className="mt-1.5"
              aria-label="수업 날짜"
            />
          </label>
          <label className="block text-sm font-medium">
            주제
            <Input
              list="studyweave-topics"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="예: LangGraph, RAG, 퀴즈"
              className="mt-1.5"
              aria-label="수업 주제"
            />
            <datalist id="studyweave-topics">
              {topics.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
          </label>
          <input
            type="file"
            accept=".pdf,.py,.js,.ts,.tsx,.md,.txt"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            className="block w-full text-sm file:mr-3 file:rounded-xl file:border-0 file:bg-lavender-soft file:px-3 file:py-2 file:text-lavender"
          />
          {error ? (
            <p role="alert" className="text-sm text-red-700">
              {error}
            </p>
          ) : null}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              취소
            </Button>
            <Button type="submit" disabled={busy}>
              {busy ? "올리는 중…" : "업로드"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
