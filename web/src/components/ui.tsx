import type { ReactNode } from 'react'
import type { Course } from '../types'
import { COLOR, COURSES } from '../courses'

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-line bg-card shadow-[0_1px_0_rgb(31_42_68/0.04)] ${className}`}>
      {children}
    </div>
  )
}

export function PageTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <header className="mb-6">
      <h1 className="font-serif text-[28px] font-semibold tracking-tight">{title}</h1>
      {sub && <p className="mt-1 text-sm text-muted">{sub}</p>}
    </header>
  )
}

export function CourseTag({ course }: { course: Course }) {
  const c = COURSES.find((x) => x.id === course)!
  return (
    <span
      className="inline-flex items-center rounded px-1.5 py-0.5 font-mono text-[11px] font-medium"
      style={{ color: COLOR[course], background: `color-mix(in srgb, ${COLOR[course]} 12%, transparent)` }}
    >
      {c.short}
    </span>
  )
}

export function CoursePicker({ value, onChange, allowAll = false }: {
  value: Course | null
  onChange: (c: Course | null) => void
  allowAll?: boolean
}) {
  const opts: (Course | null)[] = [...(allowAll ? [null] : []), ...COURSES.map((c) => c.id)]
  return (
    <div className="inline-flex rounded-lg border border-line bg-card p-0.5 text-sm">
      {opts.map((o) => {
        const active = o === value
        return (
          <button
            key={o ?? 'all'}
            onClick={() => onChange(o)}
            className={`rounded-md px-3 py-1 transition ${active ? 'bg-ink text-paper' : 'text-muted hover:text-ink'}`}
          >
            {o ? COURSES.find((c) => c.id === o)!.short : 'All'}
          </button>
        )
      })}
    </div>
  )
}

export function Thinking({ label = 'Thinking' }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-muted">
      {label}
      <span className="dots inline-flex gap-0.5">
        <span>•</span><span>•</span><span>•</span>
      </span>
    </span>
  )
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
      {message}
    </div>
  )
}
