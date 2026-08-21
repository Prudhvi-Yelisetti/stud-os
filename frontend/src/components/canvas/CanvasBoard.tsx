import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  type Node,
  type Edge,
  type NodeChange,
  type EdgeChange,
  type Connection,
  type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { canvasApi } from '../../lib/canvas'
import { NotePickerModal } from './NotePickerModal'

/** On-disk shape stored in Canvas.data (a single JSON blob -- see
 * backend/database/models/canvas.py for why). React Flow's own Node/Edge
 * types carry a lot of runtime-only fields (selected, dragging, measured
 * dimensions, callbacks in `data`) that shouldn't be persisted, so this
 * is a deliberately narrower shape that gets translated to/from React
 * Flow's types at the load/save boundary. */
interface StoredNode {
  id: string
  type: 'text' | 'note'
  x: number
  y: number
  text?: string
  chapterId?: string
  chapterTitle?: string
}
interface StoredEdge {
  id: string
  source: string
  target: string
}
interface StoredGraph {
  nodes?: StoredNode[]
  edges?: StoredEdge[]
}

function TextNode({ id, data }: NodeProps) {
  const { text, onTextChange } = data as { text: string; onTextChange: (id: string, text: string) => void }
  return (
    <div className="rounded border border-neutral-700 bg-neutral-900 p-2 shadow-lg" style={{ width: 220 }}>
      <Handle type="target" position={Position.Left} />
      <textarea
        defaultValue={text}
        onChange={(e) => onTextChange(id, e.target.value)}
        onPointerDownCapture={(e) => e.stopPropagation()} // let text-selection work without dragging the node
        placeholder="Type a note..."
        className="h-24 w-full resize-none bg-transparent text-sm text-neutral-200 outline-none placeholder:text-neutral-600"
      />
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

function NoteCardNode({ data }: NodeProps) {
  const { title, onOpen } = data as { title: string; onOpen: () => void }
  return (
    <div style={{ width: 220 }}>
      <Handle type="target" position={Position.Left} />
      <button
        onClick={onOpen}
        className="w-full rounded border border-emerald-800 bg-neutral-900 px-3 py-2 text-left text-sm text-emerald-400 shadow-lg hover:bg-neutral-800"
      >
        📄 {title}
      </button>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

const nodeTypes = { text: TextNode, note: NoteCardNode }

/** Staggers each new node diagonally so it doesn't spawn exactly on top
 * of the last one -- a fixed spawn point meant a second node landed
 * completely hidden underneath the first, looking like the "+" button
 * had silently done nothing. */
function nextSpawnPosition(existing: Node[]): { x: number; y: number } {
  const step = 40
  return { x: 120 + (existing.length % 6) * step, y: 120 + (existing.length % 6) * step }
}

export function CanvasBoard({ canvasId }: { canvasId: string }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: canvas } = useQuery({ queryKey: ['canvas', canvasId], queryFn: () => canvasApi.get(canvasId) })

  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const edgesRef = useRef<Edge[]>([])
  const [showNotePicker, setShowNotePicker] = useState(false)
  const loadedForRef = useRef<string | null>(null)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    edgesRef.current = edges
  }, [edges])

  // Typing inside a text node's textarea updates node state directly
  // (see TextNode component), bypassing React Flow's onNodesChange
  // entirely -- so this must trigger the save itself, or edits to a
  // node's text would silently never persist (a real bug this exact
  // check caught: a node saved with text: "" right after typing a full
  // sentence into it). edgesRef (not the `edges` closure) is used here
  // because this callback is embedded in node `data` at creation time
  // and never gets recreated for already-existing nodes -- a directly
  // closed-over `edges` would go stale the moment edges changed after
  // this node was created.
  const handleTextChange = useCallback((nodeId: string, text: string) => {
    setNodes((nds) => {
      const next = nds.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, text } } : n))
      scheduleSave(next, edgesRef.current)
      return next
    })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function toFlowNode(n: StoredNode): Node {
    return {
      id: n.id,
      type: n.type,
      position: { x: n.x, y: n.y },
      data:
        n.type === 'text'
          ? { text: n.text ?? '', onTextChange: handleTextChange }
          : {
              title: n.chapterTitle ?? 'Untitled',
              chapterId: n.chapterId,
              onOpen: () => navigate(`/notes?chapter=${n.chapterId}`),
            },
    }
  }

  // Load once per canvas id -- avoids clobbering in-progress local edits
  // if the query refetches (e.g. window refocus) while the user is
  // actively editing.
  useEffect(() => {
    if (!canvas || loadedForRef.current === canvas.id) return
    loadedForRef.current = canvas.id
    let graph: StoredGraph = {}
    try {
      graph = JSON.parse(canvas.data)
    } catch {
      graph = {}
    }
    setNodes((graph.nodes ?? []).map(toFlowNode))
    setEdges((graph.edges ?? []).map((e) => ({ id: e.id, source: e.source, target: e.target })))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canvas])

  const save = useMutation({
    mutationFn: (payload: string) => canvasApi.update(canvasId, { data: payload }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['canvases'] }),
  })

  function scheduleSave(nextNodes: Node[], nextEdges: Edge[]) {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => {
      const stored: StoredGraph = {
        nodes: nextNodes.map((n) => {
          const d = n.data as { text?: string; title?: string; chapterId?: string }
          return {
            id: n.id,
            type: n.type as 'text' | 'note',
            x: n.position.x,
            y: n.position.y,
            text: n.type === 'text' ? d.text : undefined,
            chapterId: n.type === 'note' ? d.chapterId : undefined,
            chapterTitle: n.type === 'note' ? d.title : undefined,
          }
        }),
        edges: nextEdges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
      }
      save.mutate(JSON.stringify(stored))
    }, 600)
  }

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setNodes((nds) => {
        const next = applyNodeChanges(changes, nds)
        scheduleSave(next, edges)
        return next
      })
    },
    [edges], // eslint-disable-line react-hooks/exhaustive-deps
  )

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      setEdges((eds) => {
        const next = applyEdgeChanges(changes, eds)
        scheduleSave(nodes, next)
        return next
      })
    },
    [nodes], // eslint-disable-line react-hooks/exhaustive-deps
  )

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => {
        const next = addEdge(connection, eds)
        scheduleSave(nodes, next)
        return next
      })
    },
    [nodes], // eslint-disable-line react-hooks/exhaustive-deps
  )

  function addTextNode() {
    const id = `n-${Date.now()}`
    setNodes((nds) => {
      const next = [...nds, toFlowNode({ id, type: 'text', ...nextSpawnPosition(nds), text: '' })]
      scheduleSave(next, edges)
      return next
    })
  }

  function addNoteNode(chapter: { id: string; title: string }) {
    const id = `n-${Date.now()}`
    setNodes((nds) => {
      const next = [
        ...nds,
        toFlowNode({ id, type: 'note', ...nextSpawnPosition(nds), chapterId: chapter.id, chapterTitle: chapter.title }),
      ]
      scheduleSave(next, edges)
      return next
    })
    setShowNotePicker(false)
  }

  return (
    <div className="relative h-full">
      <div className="absolute left-2 top-2 z-10 flex gap-2">
        <button
          onClick={addTextNode}
          className="rounded bg-neutral-800 px-3 py-1.5 text-xs text-neutral-200 shadow hover:bg-neutral-700"
        >
          + Text
        </button>
        <button
          onClick={() => setShowNotePicker(true)}
          className="rounded bg-neutral-800 px-3 py-1.5 text-xs text-neutral-200 shadow hover:bg-neutral-700"
        >
          + Note
        </button>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        colorMode="dark"
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
      {showNotePicker && <NotePickerModal onPick={addNoteNode} onClose={() => setShowNotePicker(false)} />}
    </div>
  )
}
