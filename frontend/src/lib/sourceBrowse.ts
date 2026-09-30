import type { SourceItem } from "@/lib/api";

export const STUDY_MONTHS = [
  { id: "all", label: "전체", prefix: "" },
  { id: "07", label: "7월", prefix: "2026-07" },
  { id: "08", label: "8월", prefix: "2026-08" },
  { id: "09", label: "9월", prefix: "2026-09" },
] as const;

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"] as const;

const TONES = [
  { bg: "bg-[#ece7ff]", text: "text-[#5b4cd6]" },
  { bg: "bg-[#ffe9d6]", text: "text-[#c46a1b]" },
  { bg: "bg-[#e7f4ff]", text: "text-[#2f6fad]" },
  { bg: "bg-[#e9f8ef]", text: "text-[#2d7a4f]" },
  { bg: "bg-[#fde8f1]", text: "text-[#b44a73]" },
  { bg: "bg-[#fff4c8]", text: "text-[#9a7a12]" },
] as const;

export function formatStudyDay(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate);
  if (!match) return isoDate;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  const weekday = WEEKDAYS[date.getDay()] ?? "";
  return `${Number(match[2])}월 ${Number(match[3])}일 (${weekday})`;
}

export function topicTone(topic: string) {
  let hash = 0;
  for (const char of topic) hash = (hash + char.charCodeAt(0) * 17) % TONES.length;
  return TONES[hash] ?? TONES[0];
}

export function inMonth(dateFolder: string, prefix: string) {
  if (!prefix) return true;
  return dateFolder.startsWith(prefix);
}

export function matchesQuery(source: SourceItem, query: string) {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return (
    source.topic.toLowerCase().includes(q) ||
    source.filename.toLowerCase().includes(q) ||
    source.date_folder.includes(q) ||
    source.relative_path.toLowerCase().includes(q)
  );
}

export function groupByDate(sources: SourceItem[]) {
  const map = new Map<string, SourceItem[]>();
  for (const source of sources) {
    const items = map.get(source.date_folder) ?? [];
    items.push(source);
    map.set(source.date_folder, items);
  }
  return [...map.entries()].sort((left, right) => right[0].localeCompare(left[0]));
}

export function groupByTopic(sources: SourceItem[]) {
  const map = new Map<string, SourceItem[]>();
  for (const source of sources) {
    const items = map.get(source.topic) ?? [];
    items.push(source);
    map.set(source.topic, items);
  }
  return [...map.entries()].sort((left, right) => left[0].localeCompare(right[0], "ko"));
}
