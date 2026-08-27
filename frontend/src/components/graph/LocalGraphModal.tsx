import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ReactFlow, Background, Controls, type Node, type Edge } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { graphApi } from '../../lib/search'
import type { GraphNode } from '../../lib/api'

const NODE_COLOR: Record<GraphNode['type'], string> = {
  notebook: '#6366f1',
  chapter: '#22c55e',
  project: '#f59e0b',
  task: '#ef4444',
  journal: '#38bdf8',
}

/**
 * Per-note "neighbors only" subgraph -- Obsidian's Local Graph. Reuses the
 * same /api/graph payload as the global KnowledgeGraphView (shares its
 * react-query cache under the 'graph' key, so opening this after visiting
 * the Graph page is instant) but does a BFS from the focal chapter and
 * only renders nodes within `depth` hops, radially laid out around it --
 * no dagre/elk needed for a handful of neighbors.
 *
 * Edges are treated as undirected for neighbor discovery (a wiki-link TO
 * this chapter is just as relevant a neighbor as one FROM it), matching
 * how Obsidian's local graph works.
 */
export function LocalGraphModal({
  focalId,
  onClose,
  onNavigateChapter,
}: {
  focalId: string
  onClose: () => void
  onNavigateChapter: (notebookId: string, chapterId: string) => void
}) {
  const { data } = useQuery({ queryKey: ['graph'], queryFn: graphApi.get })
  const [depth, setDepth] = useState<1 | 2>(1)

  const { nodes, edges, isEmpty } = useMemo(() => {
    if (!data) return { nodes: [] as Node[], edges: [] as Edge[], isEmpty: true }

    const nodeById = new Map(data.nodes.map((n) => [n.id, n]))
    if (!nodeById.has(focalId)) return { nodes: [] as Node[], edges: [] as Edge[], isEmpty: true }

    // Undirected adjacency for BFS.
    const neighbors = new Map<string, Set<string>>()
    for (const e of data.edges) {
      if (!neighbors.has(e.source)) neighbors.set(e.source, new Set())
      if (!neighbors.has(e.target)) neighbors.set(e.target, new Set())
      neighbors.get(e.source)!.add(e.target)
      neighbors.get(e.target)!.add(e.source)
    }

    // BFS rings up to `depth`.
    const ringOf = new Map<string, number>([[focalId, 0]])
    let frontier = [focalId]
    for (let d = 1; d <= depth; d++) {
      const next: string[] = []
      for (const id of frontier) {
        for (const nb of neighbors.get(id) ?? []) {
          if (!ringOf.has(nb)) {
            ringOf.set(nb, d)
            next.push(nb)
          }
        }
      }
      frontier = next
    }

    const visibleIds = new Set(ringOf.keys())
    const byRing = new Map<number, string[]>()
    for (const [id, ring] of ringOf) {
      if (!byRing.has(ring)) byRing.set(ring, [])
      byRing.get(ring)!.push(id)
    }

    const RING_SPACING = 180
    const flowNodes: Node[] = []
    for (const [ring, ids] of byRing) {
      ids.forEach((id, i) => {
        const gn = nodeById.get(id)
        if (!gn) return
        const isFocal = ring === 0
        const angle = ids.length > 1 ? (2 * Math.PI * i) / ids.length : 0
        const r = ring * RING_SPACING
        flowNodes.push({
          id,
          position: { x: Math.cos(angle) * r, y: Math.sin(angle) * r },
          data: { label: gn.label },
          style: {
            background: NODE_COLOR[gn.type],
            color: 'white',
            border: isFocal ? '2px solid white' : 'none',
            borderRadius: 6,
            fontSize: isFocal ? 13 : 11,
            fontWeight: isFocal ? 700 : 400,
            width: isFocal ? 200 : 160,
            opacity: isFocal ? 1 : 0.85,
          },
        })
      })
    }

    const flowEdges: Edge[] = data.edges
      .filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target))
      .map((e, i) => ({
        id: `e${i}`,
        source: e.source,
        target: e.target,
        animated: e.kind === 'wiki_link',
        style: { stroke: e.kind === 'wiki_link' ? '#22c55e' : '#525252' },
      }))

    return { nodes: flowNodes, edges: flowEdges, isEmpty: flowNodes.length <= 1 }
  }, [data, focalId, depth])

  function handleNodeClick(_: unknown, node: Node) {
    if (node.id === focalId) return
    const gn = data?.nodes.find((n) => n.id === node.id)
    if (gn?.type === 'chapter' && gn.parent_id) {
      onNavigateChapter(gn.parent_id, gn.id)
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="absolute inset-0" onClick={onClose} />
      <div className="relative flex h-[75vh] w-full max-w-3xl flex-col rounded bg-neutral-900 shadow-xl">
        <div className="flex items-center justify-between border-b border-neutral-800 p-4">
          <h2 className="text-base font-medium">Local graph</h2>
          <div className="flex items-center gap-3">
            <div className="flex overflow-hidden rounded border border-neutral-800 text-xs">
              <button
                onClick={() => setDepth(1)}
                className={`px-2 py-1 ${depth === 1 ? 'bg-neutral-700 text-white' : 'text-neutral-500 hover:text-neutral-300'}`}
              >
                1 hop
              </button>
              <button
                onClick={() => setDepth(2)}
                className={`px-2 py-1 ${depth === 2 ? 'bg-neutral-700 text-white' : 'text-neutral-500 hover:text-neutral-300'}`}
              >
                2 hops
              </button>
            </div>
            <button onClick={onClose} className="text-neutral-500 hover:text-neutral-300">
              ✕
            </button>
          </div>
        </div>
        <div className="relative flex-1">
          {isEmpty && (
            <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
              <p className="text-sm text-neutral-600">No linked notes within {depth} hop{depth > 1 ? 's' : ''} yet.</p>
            </div>
          )}
          <ReactFlow nodes={nodes} edges={edges} onNodeClick={handleNodeClick} fitView colorMode="dark">
            <Background />
            <Controls />
          </ReactFlow>
        </div>
      </div>
    </div>
  )
}
