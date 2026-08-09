import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { aiApi } from '../lib/ai'
import type { AIProviderStatus } from '../lib/api'

const DEFAULT_FEATURE = 'default'

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
        connect one below (or run a local model server like Ollama/LM Studio with nothing to configure at all),
        pick one as your default, and every feature uses it unless you override it individually.
      </p>

      <h2 className="mb-2 text-sm font-medium text-neutral-400">Providers</h2>
      <div className="mb-8 max-w-xl rounded bg-neutral-900">
        <ProvidersSection />
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

function ProvidersSection() {
  const queryClient = useQueryClient()
  const [showAddForm, setShowAddForm] = useState(false)
  const [addProvider, setAddProvider] = useState('')
  const [addKey, setAddKey] = useState('')
  const [addError, setAddError] = useState<string | null>(null)

  const { data: providers, isLoading } = useQuery({ queryKey: ['ai-providers'], queryFn: aiApi.providers })
  const { data: defaultSettings } = useQuery({
    queryKey: ['ai-settings', DEFAULT_FEATURE],
    queryFn: () => aiApi.getSettings(DEFAULT_FEATURE),
  })

  const setDefault = useMutation({
    mutationFn: (providerKey: string) => aiApi.updateSettings(DEFAULT_FEATURE, { provider_key: providerKey }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ai-settings'] }),
  })

  const connect = useMutation({
    mutationFn: () => aiApi.setProviderKey(addProvider, addKey),
    onSuccess: () => {
      setShowAddForm(false)
      setAddProvider('')
      setAddKey('')
      setAddError(null)
      queryClient.invalidateQueries({ queryKey: ['ai-providers'] })
    },
    onError: () => setAddError('Could not connect -- see the app logs for details.'),
  })

  if (isLoading) return <p className="p-4 text-sm text-neutral-600">Loading…</p>

  const connected = (providers ?? []).filter((p) => p.configured)
  const notYetConnected = (providers ?? []).filter((p) => p.requires_key && !p.configured)

  return (
    <>
      {connected.length === 0 && (
        <p className="p-4 text-sm text-neutral-600">No providers connected yet.</p>
      )}
      {connected.map((p) => (
        <ProviderRow
          key={p.key}
          provider={p}
          isDefault={defaultSettings?.provider_key === p.key}
          onSetDefault={() => setDefault.mutate(p.key)}
        />
      ))}

      <div className="p-4">
        {!showAddForm ? (
          notYetConnected.length > 0 ? (
            <button
              onClick={() => {
                setShowAddForm(true)
                setAddProvider(notYetConnected[0].key)
              }}
              className="text-sm text-neutral-400 hover:text-neutral-200"
            >
              + Add API key
            </button>
          ) : (
            <p className="text-xs text-neutral-600">Every provider that takes a key is already connected.</p>
          )
        ) : (
          <div className="flex flex-wrap gap-2">
            <select
              value={addProvider}
              onChange={(e) => setAddProvider(e.target.value)}
              className="rounded border border-neutral-700 bg-neutral-950 px-2 py-1.5 text-sm"
            >
              {notYetConnected.map((p) => (
                <option key={p.key} value={p.key}>{p.label}</option>
              ))}
            </select>
            <input
              type="password"
              value={addKey}
              onChange={(e) => setAddKey(e.target.value)}
              placeholder="API key"
              className="flex-1 rounded border border-neutral-700 bg-neutral-950 px-2 py-1.5 text-sm"
            />
            <button
              onClick={() => connect.mutate()}
              disabled={!addKey || connect.isPending}
              className="rounded bg-neutral-800 px-3 py-1.5 text-sm hover:bg-neutral-700 disabled:opacity-50"
            >
              Connect
            </button>
            <button
              onClick={() => { setShowAddForm(false); setAddError(null) }}
              className="rounded border border-neutral-700 px-3 py-1.5 text-sm text-neutral-400 hover:bg-neutral-800"
            >
              Cancel
            </button>
            {addError && <p className="w-full text-xs text-red-400">{addError}</p>}
          </div>
        )}
      </div>
    </>
  )
}

function ProviderRow({
  provider, isDefault, onSetDefault,
}: {
  provider: AIProviderStatus
  isDefault: boolean
  onSetDefault: () => void
}) {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')

  const setKey = useMutation({
    mutationFn: (apiKey: string) => aiApi.setProviderKey(provider.key, apiKey),
    onSuccess: () => {
      setEditing(false)
      setDraft('')
      queryClient.invalidateQueries({ queryKey: ['ai-providers'] })
      queryClient.invalidateQueries({ queryKey: ['ai-settings'] })
    },
  })

  return (
    <div className="border-b border-neutral-800 p-4 last:border-0">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{provider.label}</p>
          {!provider.requires_key && <p className="text-xs text-neutral-500">Runs locally -- no API key needed.</p>}
        </div>
        <div className="flex items-center gap-2">
          {isDefault ? (
            <span className="rounded bg-neutral-800 px-2 py-0.5 text-xs text-emerald-400">Default</span>
          ) : (
            <button onClick={onSetDefault} className="text-xs text-neutral-500 hover:text-neutral-300">
              Set as default
            </button>
          )}
          {provider.requires_key && !editing && (
            <>
              <button onClick={() => setEditing(true)} className="text-xs text-neutral-500 hover:text-neutral-300">
                Edit
              </button>
              <button
                onClick={() => setKey.mutate('')}
                className="text-xs text-neutral-500 hover:text-red-400"
              >
                Remove
              </button>
            </>
          )}
        </div>
      </div>
      {provider.requires_key && editing && (
        <div className="mt-2 flex gap-2">
          <input
            type="password"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="New API key"
            autoFocus
            className="flex-1 rounded border border-neutral-700 bg-neutral-950 px-2 py-1.5 text-sm"
          />
          <button
            onClick={() => setKey.mutate(draft)}
            disabled={!draft || setKey.isPending}
            className="rounded bg-neutral-800 px-3 py-1.5 text-sm hover:bg-neutral-700 disabled:opacity-50"
          >
            Save
          </button>
          <button
            onClick={() => { setEditing(false); setDraft('') }}
            className="rounded border border-neutral-700 px-3 py-1.5 text-sm text-neutral-400 hover:bg-neutral-800"
          >
            Cancel
          </button>
        </div>
      )}
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
    onError: () => setError('That provider has no API key set -- connect it above, then try again.'),
  })

  const connected = (providers ?? []).filter((p) => p.configured)
  const effectiveLabel = connected.find((p) => p.key === settings?.effective_provider_key)?.label

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
          <option value="">Use default{effectiveLabel ? ` (${effectiveLabel})` : ' (none set)'}</option>
          {connected.map((p) => (
            <option key={p.key} value={p.key}>{p.label}</option>
          ))}
        </select>
      </div>
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  )
}
