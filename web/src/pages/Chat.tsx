import { useEffect, useRef, useState } from 'react'
import { api, docUrl } from '../api'
import type { ChatReply, Part, Source } from '../types'
import { Card, ErrorNote, PageTitle, Thinking } from '../components/ui'

type Turn = { role: 'user'; text: string } | { role: 'assistant'; reply: ChatReply }

const SUGGESTIONS = [
  'Why does Dijkstra fail with negative edges?',
  'Alpha-beta complexity with perfect ordering?',
  'Explain the observer pattern',
  'What should I study next?',
]

export default function Chat() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [conv, setConv] = useState<string>()
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string>()
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns, busy])

  async function send(text: string) {
    text = text.trim()
    if (!text || busy) return
    setDraft('')
    setError(undefined)
    setTurns((t) => [...t, { role: 'user', text }])
    setBusy(true)
    try {
      const reply = await api.chat(text, conv)
      setConv(reply.conversation_id)
      setTurns((t) => [...t, { role: 'assistant', reply }])
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-4.5rem)] flex-col">
      <PageTitle
        title="Ask your notes"
        sub="Answers come from your slides, textbook chapters and notes. Every claim links to the page it came from."
      />

      <div className="flex-1 space-y-6">
        {turns.length === 0 && (
          <div className="flex flex-wrap gap-2 pt-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="rounded-full border border-line bg-card px-3.5 py-1.5 text-sm text-ink/80 hover:border-ink/30"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {turns.map((t, i) =>
          t.role === 'user' ? (
            <div key={i} className="fade-in flex justify-end">
              <div className="max-w-[70%] rounded-2xl rounded-br-md bg-ink px-4 py-2.5 text-[15px] text-paper">
                {t.text}
              </div>
            </div>
          ) : (
            <Answer key={i} reply={t.reply} />
          ),
        )}
        {busy && <Thinking label="Searching your material" />}
        {error && <ErrorNote message={error} />}
        <div ref={bottom} />
      </div>

      <form
        className="sticky bottom-0 mt-6 bg-paper/90 pb-2 pt-3 backdrop-blur"
        onSubmit={(e) => {
          e.preventDefault()
          send(draft)
        }}
      >
        <div className="flex items-end gap-2 rounded-xl border border-line bg-card p-2 focus-within:border-ink/40">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send(draft)
              }
            }}
            rows={1}
            placeholder="Ask about anything in your courses…"
            className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-[15px] outline-none placeholder:text-muted"
          />
          <button
            disabled={busy || !draft.trim()}
            className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-paper disabled:opacity-30"
          >
            Ask
          </button>
        </div>
      </form>
    </div>
  )
}

function Answer({ reply }: { reply: ChatReply }) {
  const [active, setActive] = useState<number | null>(null)
  return (
    <div className="fade-in grid gap-4 md:grid-cols-[1fr_17rem]">
      <Card className="px-5 py-4">
        <AnswerText parts={reply.parts} onRef={setActive} />
        {reply.served_by && (
          <p className="mt-3 text-xs text-muted">answered by {reply.served_by}</p>
        )}
      </Card>
      {reply.sources.length > 0 && (
        <Sources sources={reply.sources} active={active} />
      )}
    </div>
  )
}

function AnswerText({ parts, onRef }: { parts: Part[]; onRef: (n: number | null) => void }) {
  return (
    <p className="whitespace-pre-line text-[15px] leading-7">
      {parts.map((p, i) => (
        <span key={i}>
          {p.text}
          {p.refs.map((n) => (
            <a
              key={n}
              href={`#src-${n}`}
              onClick={(e) => e.preventDefault()}
              onMouseEnter={() => onRef(n)}
              onMouseLeave={() => onRef(null)}
              className="ml-0.5 align-super font-mono text-[10px] font-medium text-daa hover:underline"
            >
              {n}
            </a>
          ))}
        </span>
      ))}
    </p>
  )
}

function Sources({ sources, active }: { sources: Source[]; active: number | null }) {
  return (
    <ol className="space-y-2">
      {sources.map((s) => (
        <li
          key={s.n}
          id={`src-${s.n}`}
          className={`rounded-lg border bg-card px-3 py-2.5 text-xs transition ${
            active === s.n ? 'border-daa/60 shadow-sm' : 'border-line'
          }`}
        >
          <div className="flex items-start gap-2">
            <span className="mt-px font-mono text-[10px] font-medium text-daa">{s.n}</span>
            <div className="min-w-0">
              <a
                href={docUrl(s.source)}
                target="_blank"
                rel="noreferrer"
                className="block truncate font-medium text-ink hover:underline"
                title={s.title}
              >
                {s.title}
              </a>
              <blockquote className="mt-1 line-clamp-3 border-l-2 border-line pl-2 italic leading-snug text-muted">
                {s.quote}
              </blockquote>
            </div>
          </div>
        </li>
      ))}
    </ol>
  )
}
