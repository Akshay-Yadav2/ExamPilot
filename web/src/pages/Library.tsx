import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { Course, Doc, QueueStats } from '../types'
import { Card, CoursePicker, CourseTag, ErrorNote, PageTitle } from '../components/ui'

const STATUS: Record<Doc['status'], string> = {
  queued: 'bg-ink/5 text-ink/60',
  processing: 'bg-ai/10 text-ai',
  done: 'bg-swe/10 text-swe',
  failed: 'bg-red-50 text-red-700',
}

export default function Library() {
  const [docs, setDocs] = useState<Doc[]>([])
  const [queue, setQueue] = useState<QueueStats | null>(null)
  const [course, setCourse] = useState<Course>('daa')
  const [filter, setFilter] = useState<Course | null>(null)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState<string>()
  const [notice, setNotice] = useState<string>()
  const input = useRef<HTMLInputElement>(null)

  const refresh = useCallback(async () => {
    try {
      const r = await api.documents()
      setDocs(r.documents)
      setQueue(r.queue)
    } catch (e) {
      setError((e as Error).message)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  // poll while something is still being processed
  const inFlight = docs.some((d) => d.status === 'queued' || d.status === 'processing')
  useEffect(() => {
    if (!inFlight) return
    const t = setInterval(refresh, 2000)
    return () => clearInterval(t)
  }, [inFlight, refresh])

  async function upload(files: FileList | File[]) {
    setError(undefined)
    let queued = 0
    let dupes = 0
    for (const f of Array.from(files)) {
      if (!/\.(pdf|md)$/i.test(f.name)) continue
      try {
        const r = await api.upload(f, course)
        if (r.status === 'duplicate') dupes++
        else queued++
      } catch (e) {
        setError(`${f.name}: ${(e as Error).message}`)
      }
    }
    setNotice(`${queued} queued${dupes ? `, ${dupes} already in the library` : ''}`)
    refresh()
  }

  const shown = filter ? docs.filter((d) => d.course_id === filter) : docs
  const totals = {
    files: docs.length,
    pages: docs.reduce((s, d) => s + (d.pages ?? 0), 0),
    chunks: docs.reduce((s, d) => s + d.chunks, 0),
  }

  return (
    <div>
      <PageTitle
        title="Library"
        sub="Drop in slides, textbook chapters, practice exams or Markdown notes. Workers split them into page-sized chunks and index them."
      />

      <div className="grid gap-4 md:grid-cols-[1fr_15rem]">
        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragging(false)
            upload(e.dataTransfer.files)
          }}
          onClick={() => input.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition ${
            dragging ? 'border-ink/50 bg-card' : 'border-line hover:border-ink/30'
          }`}
        >
          <div className="font-serif text-lg">Drop PDFs or .md files here</div>
          <div className="mt-1 text-sm text-muted">or click to choose. Same file twice is ignored.</div>
          <div className="mt-4" onClick={(e) => e.stopPropagation()}>
            <span className="mr-2 text-xs text-muted">into</span>
            <CoursePicker value={course} onChange={(c) => c && setCourse(c)} />
          </div>
          <input
            ref={input}
            type="file"
            multiple
            accept=".pdf,.md"
            hidden
            onChange={(e) => e.target.files && upload(e.target.files)}
          />
        </div>

        <Card className="px-4 py-4 text-sm">
          <div className="text-[11px] font-medium uppercase tracking-wider text-muted">Ingest queue</div>
          {queue && (
            <dl className="mt-3 grid grid-cols-2 gap-y-2.5">
              <Stat label="workers" value={queue.workers} />
              <Stat label="pending" value={queue.pending} />
              <Stat label="retrying" value={queue.delayed} />
              <Stat label="dead" value={queue.dead} warn={queue.dead > 0} />
            </dl>
          )}
          <div className="mt-4 border-t border-line pt-3 font-mono text-xs text-muted">
            {totals.files} files · {totals.pages} pages · {totals.chunks} chunks
          </div>
        </Card>
      </div>

      <div className="mt-4 space-y-2">
        {error && <ErrorNote message={error} />}
        {notice && <p className="text-sm text-muted">{notice}</p>}
      </div>

      <div className="mb-3 mt-8 flex items-center justify-between">
        <h2 className="font-serif text-lg font-semibold">Documents</h2>
        <CoursePicker value={filter} onChange={setFilter} allowAll />
      </div>
      <Card className="overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-line bg-paper/60 text-left text-xs text-muted">
            <tr>
              <th className="px-4 py-2 font-medium">File</th>
              <th className="px-4 py-2 font-medium">Course</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2 text-right font-medium">Pages</th>
              <th className="px-4 py-2 text-right font-medium">Chunks</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((d) => (
              <tr key={d.id} className="border-b border-line/70 last:border-0">
                <td className="px-4 py-2.5">
                  <div className="font-mono text-[13px]">{d.filename}</div>
                  {d.error && <div className="mt-0.5 text-xs text-red-700">{d.error}</div>}
                </td>
                <td className="px-4 py-2.5"><CourseTag course={d.course_id} /></td>
                <td className="px-4 py-2.5">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS[d.status]}`}>
                    {d.status === 'processing' ? 'processing…' : d.status}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-right font-mono text-xs">{d.pages ?? '–'}</td>
                <td className="px-4 py-2.5 text-right font-mono text-xs">{d.chunks || '–'}</td>
              </tr>
            ))}
            {shown.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted">Nothing here yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  )
}

function Stat({ label, value, warn }: { label: string; value: number; warn?: boolean }) {
  return (
    <div>
      <dd className={`font-serif text-2xl font-semibold ${warn ? 'text-red-700' : ''}`}>{value}</dd>
      <dt className="text-xs text-muted">{label}</dt>
    </div>
  )
}
