import { useQuery } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'
import { Modal } from '../shared/Modal'

export function TemplatePickerModal({
  onPick,
  onClose,
  submitting,
}: {
  onPick: (templateId: string) => void
  onClose: () => void
  submitting?: boolean
}) {
  const { data: templates } = useQuery({ queryKey: ['templates'], queryFn: notebooksApi.listTemplates })

  return (
    <Modal title="New chapter from template" onClose={onClose}>
      <div className="flex flex-col gap-1">
        {templates?.map((t) => (
          <button
            key={t.id}
            disabled={submitting}
            onClick={() => onPick(t.id)}
            className="rounded px-3 py-2 text-left text-sm text-neutral-300 hover:bg-neutral-800 disabled:opacity-50"
          >
            {t.title}
          </button>
        ))}
        {templates?.length === 0 && (
          <p className="px-1 py-2 text-sm text-neutral-600">
            No templates yet — mark any chapter "Use as template" from its detail view first.
          </p>
        )}
      </div>
    </Modal>
  )
}
