import { useParams, useNavigate } from 'react-router-dom'
import { CanvasBoard } from '../components/canvas/CanvasBoard'

export function CanvasEditorPage() {
  const { canvasId } = useParams<{ canvasId: string }>()
  const navigate = useNavigate()

  if (!canvasId) return null

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-neutral-800 px-4 py-2">
        <button onClick={() => navigate('/canvas')} className="text-sm text-neutral-400 hover:text-neutral-200">
          ← All canvases
        </button>
      </div>
      <div className="flex-1">
        <CanvasBoard canvasId={canvasId} />
      </div>
    </div>
  )
}
