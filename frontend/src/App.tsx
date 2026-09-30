import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/AppShell";
import { DashboardPage } from "@/pages/Dashboard";
import { NoteDetailPage } from "@/pages/NoteDetail";
import { NotesPage } from "@/pages/Notes";
import { SourcesPage } from "@/pages/Sources";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/sources" element={<SourcesPage />} />
        <Route path="/notes" element={<NotesPage />} />
        <Route path="/notes/:noteId" element={<NoteDetailPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
