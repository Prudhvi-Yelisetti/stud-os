import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { aiApi } from '../../lib/ai'
import { MarkdownText } from '../shared/MarkdownText'

export function TaskSuggestionWidget() {
  const { data, isLoading, isError, isFetching, refetch } = useQuery({
    queryKey: ['task-suggestions'],
    queryFn: aiApi.taskSuggestions,
    // Calls a paid API per request for some providers -- don't refetch
    // on every window focus like the rest of the dashboard's widgets do.
    staleTime: 5 * 60 * 1000,
    retry: false, // a bad key won't fix itself on retry, and it's a paid call
  })

  if (isLoading) return <p className="text-sm text-neutral-600">Loading…</p>

  if (isError) {
    return (
      <p className="text-sm text-red-400">
        The request to your configured provider failed -- check the key in{' '}
        <code className="rounded bg-neutral-950 px-1">.env</code> is valid.
      </p>
    )
  }

  if (!data?.configured) {
    return (
      <p className="text-sm text-neutral-600">
        Not set up yet.{' '}
        <Link to="/settings" className="text-neutral-400 underline decoration-dotted hover:text-neutral-200">
          Add a provider in Settings
        </Link>{' '}
        to get suggestions here.
      </p>
    )
  }

  return (
    <div>
      <MarkdownText content={data.suggestion ?? ''} />
      <button
        onClick={() => refetch()}
        disabled={isFetching}
        className="mt-2 text-xs text-neutral-600 hover:text-neutral-400 disabled:opacity-50"
      >
        {isFetching ? 'Refreshing…' : 'Refresh'}
      </button>
    </div>
  )
}
