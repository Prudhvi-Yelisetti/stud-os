import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
})

export interface Notebook {
  id: string
  title: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface Chapter {
  id: string
  notebook_id: string
  title: string
  content: string
  pinned: boolean
  version: number
  created_at: string
  updated_at: string
}

export interface Backlink {
  id: string
  title: string
}

export type TaskStatus = 'backlog' | 'todo' | 'in_progress' | 'done'
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent'
export type RepeatRule = 'none' | 'daily' | 'weekly' | 'monthly'


export interface Task {
  id: string
  project_id: string | null
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  repeat_rule: RepeatRule
  scheduled_at: string | null
  due_at: string | null
  completed_at: string | null
  is_penalized: boolean
  created_at: string
  updated_at: string
}

export type Mood = 'great' | 'good' | 'okay' | 'bad' | 'terrible'

export interface JournalEntry {
  id: string
  title: string
  content: string
  mood: Mood | null
  entry_date: string
  created_at: string
  updated_at: string
}

export interface GamificationEvent {
  xp_awarded: number
  current_xp: number
  current_level: number
  did_level_up: boolean
  streak_count: number
  newly_awarded_badges: string[]
}

export interface Badge {
  name: string
  description: string
  icon: string
}

export interface Streak {
  streak_type: string
  current_count: number
  longest_count: number
  last_active_date: string | null
}

export interface Level {
  current_level: number
  current_xp: number
}

export interface GamificationProfile {
  level: Level
  streaks: Streak[]
  badges: Badge[]
}

export interface Project {
  id: string
  title: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface Subtask {
  id: string
  task_id: string
  title: string
  done: boolean
}

export interface SearchResult {
  type: 'chapter' | 'notebook' | 'task' | 'journal'
  id: string
  title: string
  snippet: string | null
}

export interface GraphNode {
  id: string
  type: 'notebook' | 'chapter' | 'task' | 'project' | 'journal'
  label: string
  parent_id: string | null
}

export interface GraphEdge {
  source: string
  target: string
  kind: 'contains' | 'wiki_link' | 'belongs_to'
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}
