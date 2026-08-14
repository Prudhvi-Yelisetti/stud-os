import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { aiApi } from '../lib/ai'
import type { AIProviderStatus } from '../lib/api'

const DEFAULT_FEATURE = 'default'

// FastAPI's HTTPException(detail=...) is what verify()/set_provider_key
// actually put the useful part in -- "invalid x-api-key", "Connection
// refused -- is Ollama running?", etc. Falling back to a generic message
// only when the backend didn't send one (network error, CORS, ...).
function errorDetail(error: unknown, fallback: string): string {
  if (isAxiosError(error) && typeof error.response?.data?.detail === 'string') {
    return error.response.data.detail
  }
  return fallback
}

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
    onError: (error) => setAddError(errorDetail(error, 'Could not connect -- see the app logs for details.')),
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
              {connect.isPending ? 'Connecting…' : 'Connect'}
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
  const [editError, setEditError] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [showModels, setShowModels] = useState(false)

  const setKey = useMutation({
    mutationFn: (apiKey: string) => aiApi.setProviderKey(provider.key, apiKey),
    onSuccess: () => {
      setEditing(false)
      setDraft('')
      setEditError(null)
      setTestResult(null)
      queryClient.invalidateQueries({ queryKey: ['ai-providers'] })
      queryClient.invalidateQueries({ queryKey: ['ai-settings'] })
    },
    onError: (error) => setEditError(errorDetail(error, 'Could not save that key -- see the app logs for details.')),
  })

  const test = useMutation({
    mutationFn: () => aiApi.verifyProvider(provider.key),
    onSuccess: () => setTestResult({ ok: true, message: 'Connected -- verified just now.' }),
    onError: (error) => setTestResult({ ok: false, message: errorDetail(error, 'Could not reach this provider.') }),
  })

  return (
    <div className="border-b border-neutral-800 p-4 last:border-0">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium">{provider.label}</p>
          <button
            onClick={() => setShowModels((v) => !v)}
            className="rounded border border-neutral-800 px-1.5 py-0.5 text-xs text-neutral-500 hover:text-neutral-300"
          >
            Models {showModels ? '▴' : '▾'}
          </button>
        </div>
        <div className="flex items-center gap-2">
          {isDefault ? (
            <span className="rounded bg-neutral-800 px-2 py-0.5 text-xs text-emerald-400">Default</span>
          ) : (
            <button onClick={onSetDefault} className="text-xs text-neutral-500 hover:text-neutral-300">
              Set as default
            </button>
          )}
          <button
            onClick={() => { setTestResult(null); test.mutate() }}
            disabled={test.isPending}
            className="text-xs text-neutral-500 hover:text-neutral-300 disabled:opacity-50"
          >
            {test.isPending ? 'Testing…' : 'Test connection'}
          </button>
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
      {!provider.requires_key && <p className="mt-0.5 text-xs text-neutral-500">Runs locally -- no API key needed.</p>}
      {testResult && (
        <p className={`mt-1 text-xs ${testResult.ok ? 'text-emerald-400' : 'text-red-400'}`}>{testResult.message}</p>
      )}
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
            {setKey.isPending ? 'Saving…' : 'Save'}
          </button>
          <button
            onClick={() => { setEditing(false); setDraft(''); setEditError(null) }}
            className="rounded border border-neutral-700 px-3 py-1.5 text-sm text-neutral-400 hover:bg-neutral-800"
          >
            Cancel
          </button>
          {editError && <p className="w-full text-xs text-red-400">{editError}</p>}
        </div>
      )}
      {showModels && <ModelsPanel providerKey={provider.key} />}
    </div>
  )
}

function ModelsPanel({ providerKey }: { providerKey: string }) {
  const queryClient = useQueryClient()
  const [showAdd, setShowAdd] = useState(false)
  const [available, setAvailable] = useState<string[] | null>(null)
  const [fetching, setFetching] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [selectedToAdd, setSelectedToAdd] = useState('')

  const { data: models } = useQuery({
    queryKey: ['ai-models', providerKey],
    queryFn: () => aiApi.addedModels(providerKey),
  })

  const addModel = useMutation({
    mutationFn: (modelId: string) => aiApi.addModel(providerKey, modelId),
    onSuccess: () => {
      setShowAdd(false)
      queryClient.invalidateQueries({ queryKey: ['ai-models', providerKey] })
    },
    onError: (error) => setFetchError(errorDetail(error, 'Could not add that model.')),
  })

  const removeModel = useMutation({
    mutationFn: (rowId: string) => aiApi.removeModel(providerKey, rowId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ai-models', providerKey] }),
  })

  const setDefaultModel = useMutation({
    mutationFn: (rowId: string) => aiApi.setDefaultModel(providerKey, rowId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ai-models', providerKey] }),
  })

  async function openAddForm() {
    setShowAdd(true)
    setFetchError(null)
    setFetching(true)
    try {
      const list = await aiApi.availableModels(providerKey)
      setAvailable(list)
      setSelectedToAdd(list[0] ?? '')
    } catch (error) {
      setFetchError(errorDetail(error, 'Could not fetch the available models for this provider.'))
      setAvailable([])
    } finally {
      setFetching(false)
    }
  }

  return (
    <div className="mt-2 rounded border border-neutral-800 bg-neutral-950 p-3">
      {(models ?? []).length === 0 && !showAdd && (
        <p className="text-xs text-neutral-600">No models added yet.</p>
      )}
      {(models ?? []).map((m) => (
        <div key={m.id} className="flex items-center justify-between gap-2 py-1">
          <span className="font-mono text-xs">{m.model_id}</span>
          <div className="flex items-center gap-2">
            {m.is_default ? (
              <span className="rounded bg-neutral-800 px-1.5 py-0.5 text-[10px] text-emerald-400">Default</span>
            ) : (
              <button
                onClick={() => setDefaultModel.mutate(m.id)}
                className="text-[10px] text-neutral-500 hover:text-neutral-300"
              >
                Set default
              </button>
            )}
            <button
              onClick={() => removeModel.mutate(m.id)}
              className="text-[10px] text-neutral-500 hover:text-red-400"
            >
              Remove
            </button>
          </div>
        </div>
      ))}

      {!showAdd ? (
        <button onClick={openAddForm} className="mt-1 text-xs text-neutral-400 hover:text-neutral-200">
          + Add model
        </button>
      ) : (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {fetching && <p className="text-xs text-neutral-600">Fetching available models…</p>}
          {fetchError && <p className="w-full text-xs text-red-400">{fetchError}</p>}
          {available && available.length > 0 && (
            <>
              <select
                value={selectedToAdd}
                onChange={(e) => setSelectedToAdd(e.target.value)}
                className="rounded border border-neutral-700 bg-neutral-950 px-2 py-1 text-xs"
              >
                {available.map((id) => (
                  <option key={id} value={id}>{id}</option>
                ))}
              </select>
              <button
                onClick={() => addModel.mutate(selectedToAdd)}
                disabled={addModel.isPending}
                className="rounded bg-neutral-800 px-2 py-1 text-xs hover:bg-neutral-700 disabled:opacity-50"
              >
                {addModel.isPending ? 'Adding…' : 'Add'}
              </button>
            </>
          )}
          {available && available.length === 0 && !fetchError && (
            <p className="text-xs text-neutral-600">This provider didn't return any models.</p>
          )}
          <button
            onClick={() => setShowAdd(false)}
            className="rounded border border-neutral-700 px-2 py-1 text-xs text-neutral-400 hover:bg-neutral-800"
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
    onError: (error) => setError(errorDetail(error, 'That provider has no API key set -- connect it above, then try again.')),
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
