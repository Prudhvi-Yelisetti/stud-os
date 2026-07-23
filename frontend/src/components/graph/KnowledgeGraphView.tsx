import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
} from '@xyflow/react'
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

export function KnowledgeGraphView() {
  const { data } = useQuery({ queryKey: ['graph'], queryFn: graphApi.get })

  const { nodes, edges } = useMemo(() => {
    if (!data) return { nodes: [] as Node[], edges: [] as Edge[] }

    // Simple column layout by type -- no layout-engine dependency needed
    // for a first pass; swap for dagre/elk later if graphs get dense.
    const typeOrder: GraphNode['type'][] = ['notebook', 'chapter', 'project', 'task', 'journal']
    const columnX: Record<string, number> = {}
    typeOrder.forEach((t, i) => (columnX[t] = i * 260))
    const rowCounters: Record<string, number> = {}

    const flowNodes: Node[] = data.nodes.map((n) => {
      const row = rowCounters[n.type] ?? 0
      rowCounters[n.type] = row + 1
      return {
        id: n.id,
        position: { x: columnX[n.type], y: row * 70 },
        data: { label: n.label },
        style: {
          background: NODE_COLOR[n.type],
          color: 'white',
          border: 'none',
          borderRadius: 6,
          fontSize: 12,
          width: 200,
        },
      }
    })

    const flowEdges: Edge[] = data.edges.map((e, i) => ({
      id: `e${i}`,
      source: e.source,
      target: e.target,
      animated: e.kind === 'wiki_link',
      style: { stroke: e.kind === 'wiki_link' ? '#22c55e' : '#525252' },
    }))

    return { nodes: flowNodes, edges: flowEdges }
  }, [data])

  const isEmpty = data && data.nodes.length === 0

  return (
    <div className="relative h-full">
      {isEmpty && (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
          <p className="text-sm text-neutral-600">
            Nothing to visualize yet — add notebooks, chapters, tasks, or projects to see them connected here.
          </p>
        </div>
      )}
      <ReactFlow nodes={nodes} edges={edges} fitView colorMode="dark">
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  )
}
