import { useEffect, useRef, useState } from 'react'

export interface DropdownMenuItem {
  label: string
  onClick: () => void
  danger?: boolean
}

export function DropdownMenu({ items }: { items: DropdownMenuItem[] }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  return (
    <div ref={ref} className="relative" onClick={(e) => e.stopPropagation()}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="rounded px-1 text-neutral-500 hover:bg-neutral-800 hover:text-neutral-300"
        title="More options"
      >
        ⋯
      </button>
      {open && (
        <div className="absolute right-0 top-full z-20 mt-1 w-40 rounded bg-neutral-800 py-1 shadow-lg">
          {items.map((item) => (
            <button
              key={item.label}
              onClick={() => {
                setOpen(false)
                item.onClick()
              }}
              className={`block w-full px-3 py-1.5 text-left text-sm hover:bg-neutral-700 ${
                item.danger ? 'text-red-400' : 'text-neutral-300'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
