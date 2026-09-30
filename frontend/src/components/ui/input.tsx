import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-11 w-full rounded-2xl border border-[#e4def3] bg-white px-4 text-sm text-ink placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lavender",
        className,
      )}
      {...props}
    />
  );
}
