import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { aiApi } from '../lib/ai'
import { notebooksApi } from '../lib/notebooks'
import { MarkdownText } from '../components/shared/MarkdownText'
import type { AskMessage, AskSource } from '../lib/api'

interface DisplayMessage extends AskMessage {
  sources?: AskSource[]
}

export function AskPage() {
  const navigate = useNavigate()
  const { data: notebooks } = useQuery({ queryKey: ['notebooks'], queryFn: notebooksApi.list })

  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [draft, setDraft] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const ask = useMutation({
    mutationFn: (history: DisplayMessage[]) =>
      aiApi.ask(
        history.map((m) => ({ role: m.role, content: m.content })),
        selectedSources,
      ),
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, ask.isPending])

  function toggleSource(id: string) {
    setSelectedSources((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]))
  }

  function send() {
    const text = draft.trim()
    if (!text || ask.isPending) return
    const nextHistory = [...messages, { role: 'user' as const, content: text }]
    setMessages(nextHistory)
    setDraft('')

    ask.mutate(nextHistory, {
      onSuccess: (resp) => {
        if (!resp.configured) return
        setMessages((prev) => [...prev, { role: 'assistant', content: resp.answer ?? '', sources: resp.sources }])
      },
    })
  }

  const notConfigured = ask.data && !ask.data.configured

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-neutral-800 p-4">
        <h1 className="mb-2 text-xl font-semibold">Ask your notes</h1>
        <div className="flex flex-wrap gap-1.5">
          {notebooks?.map((nb) => (
            <button
              key={nb.id}
              onClick={() => toggleSource(nb.id)}
              className={`rounded-full border px-2.5 py-1 text-xs ${
                selectedSources.includes(nb.id)
                  ? 'border-neutral-400 bg-neutral-800 text-neutral-100'
                  : 'border-neutral-700 text-neutral-500 hover:text-neutral-300'
              }`}
            >
              {nb.title}
            </button>
          ))}
          <button
            onClick={() => toggleSource('journal')}
            className={`rounded-full border px-2.5 py-1 text-xs ${
              selectedSources.includes('journal')
                ? 'border-neutral-400 bg-neutral-800 text-neutral-100'
                : 'border-neutral-700 text-neutral-500 hover:text-neutral-300'
            }`}
          >
            Journal
          </button>
        </div>
        <p className="mt-1.5 text-xs text-neutral-600">
          {selectedSources.length === 0 ? 'Searching everything' : `${selectedSources.length} source(s) selected`}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && !ask.isPending && (
          <p className="text-sm text-neutral-600">Ask a question about your notes or journal.</p>
        )}
        <div className="flex flex-col gap-3">
          {messages.map((m, i) => (
            <div key={i} className={m.role === 'user' ? 'ml-auto max-w-[80%]' : 'max-w-[80%]'}>
              <div className={`rounded px-3 py-2 text-sm ${m.role === 'user' ? 'bg-neutral-800' : 'bg-neutral-900'}`}>
                {m.role === 'assistant' ? <MarkdownText content={m.content} /> : m.content}
              </div>
              {m.sources && m.sources.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {m.sources.map((s) => (
                    <button
                      key={`${s.type}-${s.id}`}
                      onClick={() => navigate(s.type === 'chapter' ? `/notes?chapter=${s.id}` : '/journal')}
                      className="rounded border border-neutral-800 px-1.5 py-0.5 text-xs text-neutral-500 hover:text-neutral-300"
                    >
                      {s.title}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {ask.isPending && <p className="text-sm text-neutral-600">Thinking…</p>}

          {ask.isError && (
            <p className="text-sm text-red-400">
              The request to your configured provider failed -- check the key in{' '}
              <code className="rounded bg-neutral-900 px-1">.env</code>.
            </p>
          )}

          {notConfigured && (
            <p className="text-sm text-neutral-600">
              Not set up yet.{' '}
              <Link to="/settings" className="text-neutral-400 underline decoration-dotted hover:text-neutral-200">
                Add a provider in Settings
              </Link>
              .
            </p>
          )}
        </div>
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 border-t border-neutral-800 p-4">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Ask something…"
          className="flex-1 rounded border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm"
        />
        <button
          onClick={send}
          disabled={ask.isPending || !draft.trim()}
          className="rounded bg-neutral-800 px-4 py-2 text-sm hover:bg-neutral-700 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  )
}
