import { AlertCircle, FileQuestion, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";

export function LoadingState({ label = "불러오는 중" }: { label?: string }) {
  return (
    <div
      role="status"
      className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-3xl border border-dashed border-[#e4def3] bg-white/70 text-muted"
    >
      <LoaderCircle className="h-6 w-6 animate-spin text-lavender" />
      <p>{label}</p>
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-3xl border border-red-200 bg-red-50 px-6 text-center text-red-800"
    >
      <AlertCircle className="h-6 w-6" />
      <p className="text-sm">{message}</p>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          다시 시도
        </Button>
      ) : null}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-3xl border border-dashed border-[#e4def3] bg-white px-6 text-center">
      <FileQuestion className="h-8 w-8 text-lavender" />
      <div>
        <p className="font-medium">{title}</p>
        <p className="mt-1 text-sm text-muted">{description}</p>
      </div>
      {action}
    </div>
  );
}
