import { useState, type FormEvent } from "react";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { api, type SourceItem } from "@/lib/api";
import { useTeamUser } from "@/lib/team";

export function UploadDialog({
  open,
  onOpenChange,
  onUploaded,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUploaded: (source: SourceItem) => void;
}) {
  const { userId } = useTeamUser();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError("파일을 선택하세요.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const source = await api.uploadSource(userId, file);
      setFile(null);
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
          PDF, 파이썬/코드 파일, 텍스트를 올리면 학습 노트 초안이 만들어집니다.
        </DialogDescription>
        <form className="mt-5 space-y-4" onSubmit={(event) => void submit(event)}>
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
