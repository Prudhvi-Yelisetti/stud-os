import { useQuery } from '@tanstack/react-query'
import { gamificationApi } from '../../lib/gamification'

export function GamificationWidget() {
  const { data: profile } = useQuery({
    queryKey: ['gamification-profile'],
    queryFn: gamificationApi.profile,
  })

  if (!profile) return null

  const xpIntoLevel = profile.level.current_xp % 100
  const taskStreak = profile.streaks.find((s) => s.streak_type === 'daily_tasks')

  return (
    <div className="mt-auto border-t border-neutral-800 pt-3 text-sm">
      <div className="mb-1.5 flex items-center justify-between">
        <span className="font-medium">Level {profile.level.current_level}</span>
        <span className="text-xs text-neutral-500">{xpIntoLevel}/100 XP</span>
      </div>
      <div className="mb-2 h-1.5 w-full overflow-hidden rounded-full bg-neutral-800">
        <div className="h-full rounded-full bg-emerald-600" style={{ width: `${xpIntoLevel}%` }} />
      </div>
      {taskStreak && taskStreak.current_count > 0 && (
        <div className="mb-2 text-xs text-neutral-400">🔥 {taskStreak.current_count}-day streak</div>
      )}
      {profile.badges.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {profile.badges.map((b) => (
            <span key={b.name} title={`${b.name}: ${b.description}`} className="text-base">
              {b.icon}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
