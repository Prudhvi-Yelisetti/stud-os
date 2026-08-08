import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { aiApi } from '../lib/ai'
import type { AIProviderStatus } from '../lib/api'

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
        Semantic search always runs locally, free, with no setup. The chat-based features below need a provider --
        add a key for one (or more) below, or run a local model server (Ollama, LM Studio) with nothing to
        configure at all -- then pick one per feature.
      </p>

      <h2 className="mb-2 text-sm font-medium text-neutral-400">Providers</h2>
      <div className="mb-8 max-w-xl rounded bg-neutral-900">
        <ProviderKeyList />
      </div>

      <h2 className="mb-2 text-sm font-medium text-neutral-400">Features</h2>
      <div className="max-w-xl rounded bg-neutral-900">
        {FEATURES.map((f) => (
          <FeatureProviderPicker key={f.key} feature={f.key} label={f.label} description={f.description} />
        ))}
      </div>
    </div>
  )
}

function ProviderKeyList() {
  const { data: providers, isLoading } = useQuery({ queryKey: ['ai-providers'], queryFn: aiApi.providers })

  if (isLoading) return <p className="p-4 text-sm text-neutral-600">Loading…</p>

  return (
    <>
      {providers?.map((p) => (
        <ProviderKeyRow key={p.key} provider={p} />
      ))}
    </>
  )
}

function ProviderKeyRow({ provider }: { provider: AIProviderStatus }) {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState('')
  const [message, setMessage] = useState<string | null>(null)

  const setKey = useMutation({
    mutationFn: (apiKey: string) => aiApi.setProviderKey(provider.key, apiKey),
    onSuccess: (_, apiKey) => {
      setDraft('')
      setMessage(apiKey ? 'Saved.' : 'Removed.')
      queryClient.invalidateQueries({ queryKey: ['ai-providers'] })
    },
    onError: () => setMessage('Could not save that key -- see the app logs for details.'),
  })

  // Local servers (Ollama, LM Studio) don't check a key at all -- there's
  // nothing here for them to paste in, just a status line.
  if (!provider.requires_key) {
    return (
      <div className="flex items-center justify-between gap-3 border-b border-neutral-800 p-4 last:border-0">
        <div>
          <p className="text-sm font-medium">{provider.label}</p>
          <p className="text-xs text-neutral-500">Runs locally -- no API key needed.</p>
        </div>
        <StatusBadge configured={provider.configured} />
      </div>
    )
  }

  return (
    <div className="border-b border-neutral-800 p-4 last:border-0">
      <div className="mb-2 flex items-center justify-between gap-3">
        <p className="text-sm font-medium">{provider.label}</p>
        <StatusBadge configured={provider.configured} />
      </div>
      <div className="flex gap-2">
        <input
          type="password"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={provider.configured ? '••••••••••••  (enter a new key to replace it)' : 'Paste your API key'}
          className="flex-1 rounded border border-neutral-700 bg-neutral-950 px-2 py-1.5 text-sm"
        />
        <button
          onClick={() => setKey.mutate(draft)}
          disabled={!draft || setKey.isPending}
          className="rounded bg-neutral-800 px-3 py-1.5 text-sm hover:bg-neutral-700 disabled:opacity-50"
        >
          Save
        </button>
        {provider.configured && (
          <button
            onClick={() => setKey.mutate('')}
            disabled={setKey.isPending}
            className="rounded border border-neutral-700 px-3 py-1.5 text-sm text-neutral-400 hover:bg-neutral-800 disabled:opacity-50"
          >
            Remove
          </button>
        )}
      </div>
      {message && <p className="mt-1 text-xs text-neutral-500">{message}</p>}
    </div>
  )
}

function StatusBadge({ configured }: { configured: boolean }) {
  return (
    <span className={`text-xs ${configured ? 'text-emerald-400' : 'text-neutral-600'}`}>
      {configured ? 'Configured' : 'Not set'}
    </span>
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
    onError: () => setError('That provider has no API key set -- add one above, then try again.'),
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
