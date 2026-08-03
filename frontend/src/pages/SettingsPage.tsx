import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { aiApi } from '../lib/ai'

const FEATURES = [
  { key: 'suggestions', label: 'Task suggestions', description: 'Suggests what to work on next, based on your open tasks.' },
  { key: 'study', label: 'Study coach', description: "Generates a quiz from a chapter's content to help you study it." },
  { key: 'ask', label: 'Ask your notes', description: 'Chat that answers using your notes and journal as context.' },
]

export function SettingsPage() {
  return (
    <div className="h-full overflow-y-auto p-6">
      <h1 className="mb-1 text-xl font-semibold">Settings</h1>
      <p className="mb-6 text-sm text-neutral-500">
        Semantic search always runs locally, free, with no setup. Chat-based features below need an API key --
        add it to your <code className="rounded bg-neutral-900 px-1">.env</code> file (see{' '}
        <code className="rounded bg-neutral-900 px-1">.env.example</code>), then pick a provider here.
      </p>

      <div className="max-w-xl rounded bg-neutral-900">
        {FEATURES.map((f) => (
          <FeatureProviderPicker key={f.key} feature={f.key} label={f.label} description={f.description} />
        ))}
      </div>
    </div>
  )
}

function FeatureProviderPicker({ feature, label, description }: { feature: string; label: string; description: string }) {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const { data: providers } = useQuery({ queryKey: ['ai-providers'], queryFn: aiApi.providers })
  const { data: settings } = useQuery({
    queryKey: ['ai-settings', feature],
    queryFn: () => aiApi.getSettings(feature),
  })

  const update = useMutation({
    mutationFn: (provider_key: string | null) => aiApi.updateSettings(feature, { provider_key }),
    onSuccess: () => {
      setError(null)
      queryClient.invalidateQueries({ queryKey: ['ai-settings', feature] })
    },
    onError: () => setError('That provider has no API key set -- add it to .env first, then refresh.'),
  })

  return (
    <div className="border-b border-neutral-800 p-4 last:border-0">
      <div className="mb-1 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{label}</p>
          <p className="text-xs text-neutral-500">{description}</p>
        </div>
        <select
          value={settings?.provider_key ?? ''}
          onChange={(e) => update.mutate(e.target.value || null)}
          className="rounded border border-neutral-700 bg-neutral-950 px-2 py-1.5 text-sm"
        >
          <option value="">Not configured</option>
          {providers?.map((p) => (
            <option key={p.key} value={p.key} disabled={!p.configured}>
              {p.label}{!p.configured ? ' (no key set)' : ''}
            </option>
          ))}
        </select>
      </div>
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  )
}
