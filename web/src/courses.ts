import type { Course } from './types'

export const COURSES: { id: Course; short: string; name: string; exam: string }[] = [
  { id: 'swe', short: 'SWE', name: 'Software Engineering', exam: '2026-12-16' },
  { id: 'ai', short: 'AI', name: 'Artificial Intelligence', exam: '2026-12-17' },
  { id: 'daa', short: 'DAA', name: 'Design & Analysis of Algorithms', exam: '2026-12-21' },
]

export const COLOR: Record<Course, string> = {
  daa: 'var(--color-daa)',
  swe: 'var(--color-swe)',
  ai: 'var(--color-ai)',
}

export function daysUntil(iso: string): number {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Math.round((new Date(iso + 'T00:00:00').getTime() - today.getTime()) / 86_400_000)
}
