import { Outlet, NavLink } from 'react-router-dom'
import { GamificationWidget } from '../gamification/GamificationWidget'

const navItems = [
  { to: '/', label: 'Notes' },
  { to: '/tasks', label: 'Tasks' },
  { to: '/journal', label: 'Journal' },
]

export function AppLayout() {
  return (
    <div className="flex h-screen bg-neutral-950 text-neutral-100">
      <aside className="flex w-56 shrink-0 flex-col border-r border-neutral-800 p-4">
        <h1 className="mb-6 text-lg font-semibold tracking-tight">Stud-OS</h1>
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded px-3 py-2 text-sm ${
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
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}
