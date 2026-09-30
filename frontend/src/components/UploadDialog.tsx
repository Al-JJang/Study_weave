import { useState, type FormEvent } from "react";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, type MaterialKind, type SourceItem } from "@/lib/api";
import { MATERIAL_KINDS } from "@/lib/sourceBrowse";
import { useTeamUser } from "@/lib/team";
import { cn } from "@/lib/utils";

export function UploadDialog({
  open,
  onOpenChange,
  onUploaded,
  topics = [],
  materialKind = "lecture",
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUploaded: (items: SourceItem[], message?: string) => void;
  topics?: string[];
  materialKind?: MaterialKind;
}) {
  const { userId } = useTeamUser();
  const [file, setFile] = useState<File | null>(null);
  const [folderFiles, setFolderFiles] = useState<File[]>([]);
  const [mode, setMode] = useState<"file" | "folder">("file");
  const [topic, setTopic] = useState("");
  const [studyDate, setStudyDate] = useState("");
  const [kind, setKind] = useState<MaterialKind>(materialKind);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const copy = MATERIAL_KINDS[kind];
  const folderMode = kind === "code" && mode === "folder";
  const folderName = folderFiles[0]?.webkitRelativePath.split("/")[0] ?? "";

  const resetFiles = () => {
    setFile(null);
    setFolderFiles([]);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (folderMode) {
      if (folderFiles.length === 0) {
        setError("코드 폴더를 선택하세요.");
        return;
      }
    } else if (!file) {
      setError("파일을 선택하세요.");
      return;
    }
    if (!folderMode && !topic.trim()) {
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
      if (folderMode) {
        const result = await api.uploadCodeFolder(userId, folderFiles, {
          topic: topic.trim() || undefined,
          studyDate: studyDate.trim(),
        });
        resetFiles();
        setTopic("");
        setStudyDate("");
        onOpenChange(false);
        onUploaded(result.items, result.message);
      } else if (file) {
        const source = await api.uploadSource(userId, file, {
          topic: topic.trim(),
          studyDate: studyDate.trim(),
          materialKind: kind,
        });
        resetFiles();
        setTopic("");
        setStudyDate("");
        onOpenChange(false);
        onUploaded([source]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "업로드에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) {
          setKind(materialKind);
          setMode(materialKind === "code" ? "folder" : "file");
          resetFiles();
          setError(null);
        }
        onOpenChange(next);
      }}
    >
      <DialogContent>
        <DialogTitle>{copy.uploadLabel}</DialogTitle>
        <DialogDescription>
          {kind === "code"
            ? "강사님 코드만 올립니다. 폴더를 통째로 고르면 AI가 파일 내용을 보고 주제로 나눠 저장합니다. 노트는 만들지 않습니다."
            : "강사님 강의자료만 올립니다. 날짜와 주제를 넣으면 7월–10월 일정에 맞춰 팀이 같이 봅니다. 노트는 만들지 않습니다."}
        </DialogDescription>
        <form className="mt-5 space-y-4" onSubmit={(event) => void submit(event)}>
          <fieldset>
            <legend className="text-sm font-medium">자료 종류</legend>
            <div className="mt-1.5 grid grid-cols-2 gap-2" role="group" aria-label="자료 종류">
              {(Object.values(MATERIAL_KINDS) as (typeof MATERIAL_KINDS)[MaterialKind][]).map((item) => (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={kind === item.id}
                  onClick={() => {
                    setKind(item.id);
                    setMode(item.id === "code" ? "folder" : "file");
                    resetFiles();
                  }}
                  className={cn(
                    "rounded-2xl border px-3 py-2 text-sm font-medium",
                    kind === item.id
                      ? "border-lavender bg-lavender-soft text-lavender"
                      : "border-[#e4def3] bg-white text-muted",
                  )}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </fieldset>
          {kind === "code" ? (
            <div className="inline-flex rounded-2xl bg-cream p-1" role="group" aria-label="업로드 방식">
              <button
                type="button"
                aria-pressed={mode === "folder"}
                onClick={() => {
                  setMode("folder");
                  resetFiles();
                }}
                className={cn(
                  "rounded-xl px-3 py-1.5 text-sm font-medium",
                  mode === "folder" ? "bg-white text-lavender shadow-sm" : "text-muted",
                )}
              >
                폴더
              </button>
              <button
                type="button"
                aria-pressed={mode === "file"}
                onClick={() => {
                  setMode("file");
                  resetFiles();
                }}
                className={cn(
                  "rounded-xl px-3 py-1.5 text-sm font-medium",
                  mode === "file" ? "bg-white text-lavender shadow-sm" : "text-muted",
                )}
              >
                파일
              </button>
            </div>
          ) : null}
          <label className="block text-sm font-medium">
            수업 날짜
            <Input
              type="date"
              min="2026-07-21"
              max="2026-10-31"
              value={studyDate}
              onChange={(event) => setStudyDate(event.target.value)}
              className="mt-1.5"
              aria-label="수업 날짜"
            />
          </label>
          <label className="block text-sm font-medium">
            주제{folderMode ? " (비우면 AI가 분류)" : ""}
            <Input
              list="studyweave-topics"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder={folderMode ? "비우면 파일 보고 자동 분류" : "예: LangGraph, RAG, 퀴즈"}
              className="mt-1.5"
              aria-label="수업 주제"
            />
            <datalist id="studyweave-topics">
              {topics.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
          </label>
          {folderMode ? (
            <label className="block text-sm font-medium">
              코드 폴더
              <input
                type="file"
                multiple
                className="mt-1.5 block w-full text-sm file:mr-3 file:rounded-xl file:border-0 file:bg-lavender-soft file:px-3 file:py-2 file:text-lavender"
                aria-label="코드 폴더"
                ref={(element) => {
                  if (!element) return;
                  element.setAttribute("webkitdirectory", "");
                  element.setAttribute("directory", "");
                }}
                onChange={(event) => setFolderFiles(Array.from(event.target.files ?? []))}
              />
              {folderFiles.length > 0 ? (
                <p className="mt-1.5 text-xs text-muted">
                  {folderName} · {folderFiles.length}개 파일
                </p>
              ) : (
                <p className="mt-1.5 text-xs text-muted">수업 때 받은 코드 폴더를 그대로 고르세요.</p>
              )}
            </label>
          ) : (
            <input
              type="file"
              accept={copy.accept}
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="block w-full text-sm file:mr-3 file:rounded-xl file:border-0 file:bg-lavender-soft file:px-3 file:py-2 file:text-lavender"
            />
          )}
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
              {busy ? (folderMode ? "AI가 분류하는 중…" : "올리는 중…") : "업로드"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
