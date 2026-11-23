export type Course = 'daa' | 'swe' | 'ai'

export type Part = { text: string; refs: number[] }
export type Source = { n: number; source: string; title: string; quote: string }

export type ChatReply = {
  conversation_id: string
  parts: Part[]
  sources: Source[]
  served_by?: string | null
  refused?: boolean
}

export type Question = {
  id: string
  topic_id: string
  topic_name: string
  kind: 'mcq' | 'short'
  question: string
  choices: string[]
  reason: 'review' | 'practice'
  reason_text: string
}

export type AnswerResult = {
  score: number
  max_score: number
  feedback: string
  missing_points: string[]
  answer: string
  explanation: string
  sources: { title: string; source: string }[]
}

export type Doc = {
  id: string
  filename: string
  course_id: Course
  status: 'queued' | 'processing' | 'done' | 'failed'
  pages: number | null
  chunks: number
  error: string | null
}

export type QueueStats = { pending: number; delayed: number; dead: number; workers: number }

export type TopicRow = {
  id: string
  name: string
  course_id: Course
  attempts: number
  mastery: number
  priority: number
}

export type Progress = {
  weakest: TopicRow[]
  mastery: TopicRow[]
  daily: { day: string; answered: number; accuracy: number | null }[]
  spend: { kind: string; calls: number; usd: number; avg_ms: number; cache_hit: number | null }[]
  queue: QueueStats
}
