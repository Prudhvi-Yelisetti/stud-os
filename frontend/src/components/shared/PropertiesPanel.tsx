import { useEffect, useRef, useState } from 'react'

/** Renders a property value for the editable text input -- lists/objects
 * show as their JSON form so multi-value properties (like `tags: [...]`)
 * stay editable without a bespoke widget per value type. */
function valueToInputText(value: unknown): string {
  if (typeof value === 'string') return value
  return JSON.stringify(value)
}

/** Reverses valueToInputText: tries JSON first (so "[\"a\",\"b\"]" or "true"
 * or "3" round-trip to their real types), falls back to the raw string
 * for anything that isn't valid JSON (the common case -- "draft", "in
 * progress", etc). */
function inputTextToValue(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export function PropertiesPanel({
  properties,
  onSave,
}: {
  properties: Record<string, unknown>
  onSave: (properties: Record<string, unknown>) => void
}) {
  const [rows, setRows] = useState<{ key: string; value: string }[]>([])

  // Re-sync from the server whenever the underlying chapter/entry changes
  // (e.g. navigating to a different note) -- but not on every keystroke,
  // since this is locally-edited draft state until a row is committed.
  useEffect(() => {
    setRows(Object.entries(properties).map(([key, value]) => ({ key, value: valueToInputText(value) })))
  }, [properties])

  function commit(nextRows: { key: string; value: string }[]) {
    const next: Record<string, unknown> = {}
    for (const row of nextRows) {
      const key = row.key.trim()
      if (key) next[key] = inputTextToValue(row.value)
    }
    onSave(next)
  }

  function updateRow(index: number, field: 'key' | 'value', newValue: string) {
    setRows((prev) => prev.map((r, i) => (i === index ? { ...r, [field]: newValue } : r)))
  }

  function removeRow(index: number) {
    const nextRows = rows.filter((_, i) => i !== index)
    setRows(nextRows)
    commit(nextRows)
  }

  function addRow() {
    setRows((prev) => [...prev, { key: '', value: '' }])
  }

  return (
    <div className="mt-4 border-t border-neutral-800 pt-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-medium text-neutral-500">Properties</h3>
        <button onClick={addRow} className="text-xs text-neutral-400 hover:text-neutral-200">
          + Add property
        </button>
      </div>
      <div className="flex flex-col gap-1">
        {rows.map((row, i) => (
          <PropertyRow
            key={i}
            row={row}
            onChange={(field, value) => updateRow(i, field, value)}
            onCommit={() => commit(rows)}
            onRemove={() => removeRow(i)}
          />
        ))}
        {rows.length === 0 && <p className="text-xs text-neutral-600">No properties</p>}
      </div>
    </div>
  )
}

/** Each row is its own component so the blur check below can see both of
 * its own inputs via a ref -- a top-level per-input onBlur can't tell
 * "the user tabbed from key to value in the same row" (don't commit yet)
 * from "the user is done with this row" (commit), and committing on the
 * former was a real bug: it saved whatever the *other* field held at
 * that instant -- typically still empty -- before the user finished
 * typing it. */
function PropertyRow({
  row,
  onChange,
  onCommit,
  onRemove,
}: {
  row: { key: string; value: string }
  onChange: (field: 'key' | 'value', value: string) => void
  onCommit: () => void
  onRemove: () => void
}) {
  const rowRef = useRef<HTMLDivElement>(null)

  function handleBlur(e: React.FocusEvent) {
    const nextFocused = e.relatedTarget
    if (nextFocused instanceof Node && rowRef.current?.contains(nextFocused)) {
      return // focus moved to the sibling key/value input in this same row -- not done yet
    }
    onCommit()
  }

  return (
    <div ref={rowRef} className="flex items-center gap-1">
      <input
        value={row.key}
        onChange={(e) => onChange('key', e.target.value)}
        onBlur={handleBlur}
        placeholder="key"
        className="w-1/3 rounded bg-neutral-900 px-2 py-1 text-xs text-neutral-300 outline-none placeholder:text-neutral-600"
      />
      <input
        value={row.value}
        onChange={(e) => onChange('value', e.target.value)}
        onBlur={handleBlur}
        placeholder="value"
        className="flex-1 rounded bg-neutral-900 px-2 py-1 text-xs text-neutral-300 outline-none placeholder:text-neutral-600"
      />
      <button onClick={onRemove} className="text-neutral-600 hover:text-red-400" title="Remove">
        ✕
      </button>
    </div>
  )
}
