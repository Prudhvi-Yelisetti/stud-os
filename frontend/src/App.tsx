import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppLayout } from './components/layout/AppLayout'

// Route-level code splitting -- each page becomes its own chunk instead of
// one ~536KB bundle. GraphPage (React Flow) and the pptx-scale dependency
// surface elsewhere were the main contributors; this also means visiting
// only e.g. Tasks never downloads the graph library at all.
const NotesPage = lazy(() => import('./pages/NotesPage').then((m) => ({ default: m.NotesPage })))
const TasksPage = lazy(() => import('./pages/TasksPage').then((m) => ({ default: m.TasksPage })))
const JournalPage = lazy(() => import('./pages/JournalPage').then((m) => ({ default: m.JournalPage })))
const ProjectsPage = lazy(() => import('./pages/ProjectsPage').then((m) => ({ default: m.ProjectsPage })))
const GraphPage = lazy(() => import('./pages/GraphPage').then((m) => ({ default: m.GraphPage })))
const TagsPage = lazy(() => import('./pages/TagsPage').then((m) => ({ default: m.TagsPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })))
const TimelinePage = lazy(() => import('./pages/TimelinePage').then((m) => ({ default: m.TimelinePage })))
const TrashPage = lazy(() => import('./pages/TrashPage').then((m) => ({ default: m.TrashPage })))
const SettingsPage = lazy(() => import('./pages/SettingsPage').then((m) => ({ default: m.SettingsPage })))
const AskPage = lazy(() => import('./pages/AskPage').then((m) => ({ default: m.AskPage })))

const queryClient = new QueryClient()

function PageFallback() {
  return <div className="p-6 text-sm text-neutral-600">Loading…</div>
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/notes" element={<NotesPage />} />
              <Route path="/tasks" element={<TasksPage />} />
              <Route path="/journal" element={<JournalPage />} />
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/graph" element={<GraphPage />} />
              <Route path="/tags" element={<TagsPage />} />
              <Route path="/tags/:tagName" element={<TagsPage />} />
              <Route path="/timeline" element={<TimelinePage />} />
              <Route path="/trash" element={<TrashPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/ask" element={<AskPage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
