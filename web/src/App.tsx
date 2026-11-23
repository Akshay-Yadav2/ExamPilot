import { useEffect, useState } from 'react'
import { DEMO, getToken, setToken } from './api'
import { COLOR, COURSES, daysUntil } from './courses'
import Chat from './pages/Chat'
import Quiz from './pages/Quiz'
import Library from './pages/Library'
import ProgressPage from './pages/Progress'

const PAGES = {
  chat: { label: 'Ask', hint: 'cited answers', el: Chat },
  quiz: { label: 'Quiz', hint: 'what you\'re weak at', el: Quiz },
  library: { label: 'Library', hint: 'PDFs & notes', el: Library },
  progress: { label: 'Progress', hint: 'mastery & spend', el: ProgressPage },
} as const
type PageKey = keyof typeof PAGES

function currentPage(): PageKey {
  const h = window.location.hash.slice(1)
  return h in PAGES ? (h as PageKey) : 'chat'
}

export default function App() {
  const [page, setPage] = useState<PageKey>(currentPage)
  const [showSettings, setShowSettings] = useState(false)

  useEffect(() => {
    const onHash = () => setPage(currentPage())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const Page = PAGES[page].el

  return (
    <div className="flex h-full">
      <aside className="flex w-60 shrink-0 flex-col border-r border-line bg-[#efe9dc]/60 px-4 py-5">
        <div className="flex items-center gap-2.5 px-2">
          <img src="/favicon.svg" alt="" className="h-7 w-7" />
          <div>
            <div className="font-serif text-lg font-semibold leading-none">ExamPilot</div>
            <div className="mt-1 text-[11px] text-muted">study over your own slides</div>
          </div>
        </div>

        <nav className="mt-8 space-y-0.5">
          {(Object.keys(PAGES) as PageKey[]).map((k) => (
            <a
              key={k}
              href={`#${k}`}
              className={`flex items-baseline justify-between rounded-lg px-3 py-2 text-sm transition ${
                page === k ? 'bg-card font-medium shadow-sm' : 'text-ink/70 hover:bg-card/60'
              }`}
            >
              {PAGES[k].label}
              <span className="text-[11px] font-normal text-muted">{PAGES[k].hint}</span>
            </a>
          ))}
        </nav>

        <div className="mt-8 px-2">
          <div className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted">Finals</div>
          <ul className="space-y-2.5">
            {COURSES.map((c) => {
              const d = daysUntil(c.exam)
              return (
                <li key={c.id} className="flex items-center gap-2.5 text-sm">
                  <span className="h-2 w-2 rounded-full" style={{ background: COLOR[c.id] }} />
                  <span className="flex-1">{c.short}</span>
                  <span className="font-mono text-xs text-muted">
                    {d > 0 ? `${d}d` : d === 0 ? 'today' : 'done'}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>

        <div className="mt-auto space-y-2 px-2 text-xs text-muted">
          {DEMO && (
            <div className="rounded-md border border-dashed border-ai/50 bg-ai/5 px-2 py-1.5 text-[11px] text-ai">
              Demo mode: sample data, no backend
            </div>
          )}
          <button onClick={() => setShowSettings((s) => !s)} className="hover:text-ink">
            Settings
          </button>
          {showSettings && <TokenField onDone={() => setShowSettings(false)} />}
        </div>
      </aside>

      <main className="ruled flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-10 py-9">
          <Page />
        </div>
      </main>
    </div>
  )
}

function TokenField({ onDone }: { onDone: () => void }) {
  const [value, setValue] = useState(getToken())
  return (
    <form
      className="space-y-1.5"
      onSubmit={(e) => {
        e.preventDefault()
        setToken(value.trim())
        onDone()
      }}
    >
      <label className="block text-[11px]">API token</label>
      <input
        type="password"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="w-full rounded border border-line bg-card px-2 py-1 font-mono text-xs text-ink"
        placeholder="EXAMPILOT_TOKEN"
      />
      <button className="rounded bg-ink px-2 py-1 text-[11px] text-paper">Save</button>
    </form>
  )
}
