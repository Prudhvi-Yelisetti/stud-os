import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppLayout } from './components/layout/AppLayout'
import { NotesPage } from './pages/NotesPage'
import { TasksPage } from './pages/TasksPage'
import { JournalPage } from './pages/JournalPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { GraphPage } from './pages/GraphPage'
import { DashboardPage } from './pages/DashboardPage'
import { TimelinePage } from './pages/TimelinePage'
import { TrashPage } from './pages/TrashPage'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/notes" element={<NotesPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/journal" element={<JournalPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/graph" element={<GraphPage />} />
            <Route path="/timeline" element={<TimelinePage />} />
            <Route path="/trash" element={<TrashPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
