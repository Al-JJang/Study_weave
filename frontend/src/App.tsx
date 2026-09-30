import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/AppShell";
import { TeamUserProvider } from "@/lib/team";
import { DashboardPage } from "@/pages/Dashboard";
import { DeskPage } from "@/pages/Desk";
import { NoteDetailPage } from "@/pages/NoteDetail";
import { NotesPage } from "@/pages/Notes";
import { SourcesPage } from "@/pages/Sources";

export default function App() {
  return (
    <TeamUserProvider>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/u/:userId" element={<DeskPage />} />
          <Route path="/sources" element={<Navigate to="/sources/lectures" replace />} />
          <Route path="/sources/:kind" element={<SourcesPage />} />
          <Route path="/notes" element={<NotesPage />} />
          <Route path="/notes/:noteId" element={<NoteDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </TeamUserProvider>
  );
}
