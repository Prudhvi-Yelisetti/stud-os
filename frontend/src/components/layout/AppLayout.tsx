import { useEffect, useState } from 'react'
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { GamificationWidget } from '../gamification/GamificationWidget'
import { GlobalSearch } from '../search/GlobalSearch'
import { CommandPalette } from '../shared/CommandPalette'
import { dailyNotesApi } from '../../lib/dailyNotes'

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/notes', label: 'Notes' },
  { to: '/tasks', label: 'Tasks' },
  { to: '/journal', label: 'Journal' },
  { to: '/projects', label: 'Projects' },
  { to: '/graph', label: 'Graph' },
  { to: '/tags', label: 'Tags' },
  { to: '/canvas', label: 'Canvas' },
  { to: '/timeline', label: 'Timeline' },
  { to: '/trash', label: 'Trash' },
  { to: '/ask', label: 'Ask' },
  { to: '/settings', label: 'Settings' },
]

export function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  // Close the drawer automatically on navigation instead of requiring an
  // explicit tap outside it -- the common mobile-nav pattern.
  useEffect(() => setMobileMenuOpen(false), [location.pathname])

  return (
    <div className="flex h-screen bg-neutral-950 text-neutral-100">
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <aside
        className={`${mobileMenuOpen ? 'flex' : 'hidden'} fixed inset-y-0 left-0 z-40 w-64 flex-col
          border-r border-neutral-800 bg-neutral-950 p-4 md:static md:z-auto md:flex md:w-56`}
      >
        <h1 className="mb-6 text-xl font-semibold tracking-tight">Stud-OS</h1>
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `rounded px-3 py-2 text-base ${
                  isActive ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:bg-neutral-900'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <GamificationWidget />
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex shrink-0 items-center gap-3 border-b border-neutral-800 px-4 py-2">
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="rounded p-1.5 text-neutral-400 hover:bg-neutral-900 md:hidden"
            aria-label="Open menu"
          >
            ☰
          </button>
          <div className="flex-1 md:hidden" />
          <button
            onClick={() => dailyNotesApi.today().then((ch) => navigate(`/notes?chapter=${ch.id}`))}
            className="rounded px-2 py-1 text-sm text-neutral-400 hover:bg-neutral-900 hover:text-neutral-200"
            title="Open today's daily note"
          >
            📅 Today
          </button>
          <div className="ml-auto">
            <GlobalSearch />
          </div>
        </header>
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
      <CommandPalette />
    </div>
  )
}
