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
