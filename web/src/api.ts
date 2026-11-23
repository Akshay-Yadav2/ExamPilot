import type { AnswerResult, ChatReply, Course, Doc, Progress, Question, QueueStats } from './types'
import * as demo from './demo'

export const DEMO = import.meta.env.VITE_DEMO === 'true'

const TOKEN_KEY = 'exampilot.token'
export const getToken = () => localStorage.getItem(TOKEN_KEY) ?? ''
export const setToken = (t: string) => localStorage.setItem(TOKEN_KEY, t)

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { Authorization: `Bearer ${getToken()}`, ...(init.headers ?? {}) },
  })
  if (res.status === 401) throw new Error('Wrong or missing token. Set it under Settings.')
  if (!res.ok) throw new Error((await res.text()) || `${res.status} ${res.statusText}`)
  return res.json()
}

const json = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = DEMO
  ? demo.api
  : {
      chat: (message: string, conversation_id?: string) =>
        call<ChatReply>('/chat', json({ message, conversation_id })),

      nextQuestion: (course: Course) =>
        call<Question>(`/quiz/next?course=${course}`, { method: 'POST' }),

      answer: (question_id: string, answer: string) =>
        call<AnswerResult>('/quiz/answer', json({ question_id, answer })),

      documents: () => call<{ documents: Doc[]; queue: QueueStats }>('/documents'),

      upload: (file: File, course: Course) => {
        const form = new FormData()
        form.append('course', course)
        form.append('file', file)
        return call<{ document_id: string; status: string }>('/documents', {
          method: 'POST',
          body: form,
        })
      },

      progress: (course?: Course) =>
        call<Progress>(`/progress${course ? `?course=${course}` : ''}`),
    }

// "<doc_id>/lec14.pdf#page=22" -> "/api/files/<doc_id>#page=22"
export function docUrl(source: string): string {
  if (DEMO) return '#'
  const [docId] = source.split('/', 1)
  const page = source.split('#page=')[1]
  return `/api/files/${docId}${page ? `#page=${page}` : ''}`
}
