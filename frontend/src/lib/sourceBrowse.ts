import type { MaterialKind, SourceItem } from "@/lib/api";

export const STUDY_MONTHS = [
  { id: "all", label: "전체", prefix: "" },
  { id: "07", label: "7월", prefix: "2026-07" },
  { id: "08", label: "8월", prefix: "2026-08" },
  { id: "09", label: "9월", prefix: "2026-09" },
  { id: "10", label: "10월", prefix: "2026-10" },
] as const;

export const MATERIAL_KINDS = {
  lecture: {
    id: "lecture" as const,
    label: "강의자료",
    path: "/sources/lectures",
    emptyTitle: "아직 강의자료가 없습니다",
    emptyDescription: "강사님 슬라이드나 PDF를 올리면 팀이 같이 볼 수 있습니다.",
    uploadLabel: "강의자료 올리기",
    searchLabel: "강의자료 검색",
    loadingLabel: "강의자료를 불러오는 중",
    accept: ".pdf,.md,.txt,.ppt,.pptx",
  },
  code: {
    id: "code" as const,
    label: "코드",
    path: "/sources/code",
    emptyTitle: "아직 코드가 없습니다",
    emptyDescription: "강사님이 보여 주신 코드를 올리면 팀이 같이 볼 수 있습니다.",
    uploadLabel: "코드 올리기",
    searchLabel: "코드 검색",
    loadingLabel: "코드를 불러오는 중",
    accept: ".py,.js,.ts,.tsx,.jsx,.java,.go,.rs,.c,.cpp,.ipynb,.txt",
  },
} as const;

export function parseMaterialKind(raw: string | undefined): MaterialKind {
  return raw === "code" ? "code" : "lecture";
}

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
