import { useEffect } from 'react'

export function Modal({
  title,
  onClose,
  children,
}: {
  title: string
  onClose: () => void
  children: React.ReactNode
}) {
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="absolute inset-0" onClick={onClose} />
      <div className="relative w-full max-w-md rounded bg-neutral-900 p-5 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-medium">{title}</h2>
          <button onClick={onClose} className="text-neutral-500 hover:text-neutral-300">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
