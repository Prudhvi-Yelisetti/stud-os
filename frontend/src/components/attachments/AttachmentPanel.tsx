import { useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { attachmentsApi } from '../../lib/attachments'

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function AttachmentPanel({
  ownerType,
  ownerId,
}: {
  ownerType: 'chapter' | 'project' | 'journal'
  ownerId: string
}) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const queryKey = ['attachments', ownerType, ownerId]

  const { data: attachments } = useQuery({
    queryKey,
    queryFn: () => attachmentsApi.list(ownerType, ownerId),
  })

  const upload = useMutation({
    mutationFn: (file: File) => attachmentsApi.upload(ownerType, ownerId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  })

  const remove = useMutation({
    mutationFn: (id: string) => attachmentsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  })

  return (
    <div className="mt-4 border-t border-neutral-800 pt-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-medium text-neutral-500">Attachments</h3>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="text-xs text-neutral-400 hover:text-neutral-200"
        >
          + Add file
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) upload.mutate(file)
            e.target.value = ''
          }}
        />
      </div>
      <div className="flex flex-col gap-1">
        {attachments?.map((a) => (
          <div key={a.id} className="flex items-center justify-between rounded bg-neutral-900 px-2 py-1.5 text-xs">
            <a
              href={attachmentsApi.downloadUrl(a.id)}
              target="_blank"
              rel="noreferrer"
              className="flex-1 truncate text-neutral-300 hover:underline"
            >
              📎 {a.filename}
            </a>
            <span className="mx-2 text-neutral-600">{formatBytes(a.size_bytes)}</span>
            <button onClick={() => remove.mutate(a.id)} className="text-neutral-600 hover:text-red-400">
              ✕
            </button>
          </div>
        ))}
        {attachments?.length === 0 && <p className="text-xs text-neutral-600">No attachments</p>}
      </div>
    </div>
  )
}
