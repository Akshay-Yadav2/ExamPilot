import { useEffect, useState } from 'react'
import { api, docUrl } from '../api'
import type { AnswerResult, Course, Question } from '../types'
import { Card, CoursePicker, CourseTag, ErrorNote, PageTitle, Thinking } from '../components/ui'

export default function Quiz() {
  const [course, setCourse] = useState<Course>('swe')
  const [q, setQ] = useState<Question | null>(null)
  const [choice, setChoice] = useState('')
  const [text, setText] = useState('')
  const [result, setResult] = useState<AnswerResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [grading, setGrading] = useState(false)
  const [error, setError] = useState<string>()
  const [tally, setTally] = useState({ got: 0, of: 0 })

  async function next(c: Course = course) {
    setLoading(true)
    setError(undefined)
    setResult(null)
    setChoice('')
    setText('')
    try {
      setQ(await api.nextQuestion(c))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    next(course)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [course])

  async function submit() {
    if (!q) return
    const answer = q.kind === 'mcq' ? choice : text
    if (!answer.trim()) return
    setGrading(true)
    try {
      const r = await api.answer(q.id, answer)
      setResult(r)
      setTally((t) => ({ got: t.got + r.score, of: t.of + r.max_score }))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setGrading(false)
    }
  }

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <PageTitle
          title="Quiz"
          sub="Questions come from your own material. The scheduler leans toward topics you keep missing."
        />
        <div className="flex items-center gap-4 pt-1">
          {tally.of > 0 && (
            <span className="font-mono text-xs text-muted">
              session {tally.got}/{tally.of}
            </span>
          )}
          <CoursePicker value={course} onChange={(c) => c && setCourse(c)} />
        </div>
      </div>

      {error && <ErrorNote message={error} />}
      {loading && <Thinking label="Picking a question" />}

      {q && !loading && (
        <Card className="fade-in overflow-hidden">
          <div className="flex items-center gap-2 border-b border-line bg-paper/60 px-6 py-2.5 text-xs">
            <CourseTag course={course} />
            <span className="text-muted">{q.topic_name}</span>
            <span className="ml-auto rounded-full bg-ink/5 px-2 py-0.5 text-ink/70">
              {q.reason === 'review' ? '↻ ' : ''}
              {q.reason_text}
            </span>
          </div>

          <div className="px-6 py-5">
            <p className="font-serif text-xl leading-snug">{q.question}</p>

            {q.kind === 'mcq' ? (
              <div className="mt-5 space-y-2">
                {q.choices.map((c, i) => {
                  const picked = choice === c
                  const isAnswer = result && c === result.answer
                  const wrongPick = result && picked && !isAnswer
                  return (
                    <label
                      key={c}
                      className={`flex cursor-pointer items-start gap-3 rounded-lg border px-4 py-3 text-[15px] transition ${
                        isAnswer
                          ? 'border-swe bg-swe/5'
                          : wrongPick
                            ? 'border-red-300 bg-red-50'
                            : picked
                              ? 'border-ink/50 bg-ink/[0.03]'
                              : 'border-line hover:border-ink/25'
                      }`}
                    >
                      <input
                        type="radio"
                        name="choice"
                        className="mt-1 accent-ink"
                        checked={picked}
                        disabled={!!result}
                        onChange={() => setChoice(c)}
                      />
                      <span className="mr-1 font-mono text-xs text-muted">{'abcd'[i]}</span>
                      <span>{c}</span>
                    </label>
                  )
                })}
              </div>
            ) : (
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                disabled={!!result}
                rows={5}
                placeholder="Answer in a few sentences, like you would on the exam."
                className="mt-5 w-full rounded-lg border border-line bg-paper/40 px-4 py-3 text-[15px] leading-relaxed outline-none focus:border-ink/40"
              />
            )}

            <div className="mt-5 flex items-center gap-3">
              {!result ? (
                <button
                  onClick={submit}
                  disabled={grading || !(q.kind === 'mcq' ? choice : text.trim())}
                  className="rounded-lg bg-ink px-5 py-2 text-sm font-medium text-paper disabled:opacity-30"
                >
                  {grading ? 'Grading…' : 'Submit'}
                </button>
              ) : (
                <button
                  onClick={() => next()}
                  className="rounded-lg bg-ink px-5 py-2 text-sm font-medium text-paper"
                >
                  Next question →
                </button>
              )}
              {grading && q.kind === 'short' && <Thinking label="Comparing with the reference answer" />}
            </div>
          </div>

          {result && <Feedback result={result} kind={q.kind} />}
        </Card>
      )}
    </div>
  )
}

function Feedback({ result, kind }: { result: AnswerResult; kind: Question['kind'] }) {
  const tone =
    result.score === result.max_score ? 'text-swe' : result.score === 0 ? 'text-red-700' : 'text-ai'
  const label =
    result.score === result.max_score ? 'Correct' : result.score === 0 ? 'Not quite' : 'Partly right'
  return (
    <div className="fade-in border-t border-line bg-paper/50 px-6 py-5 text-sm">
      <div className="flex items-baseline gap-3">
        <span className={`font-serif text-lg font-semibold ${tone}`}>{label}</span>
        <span className="font-mono text-xs text-muted">
          {result.score}/{result.max_score}
        </span>
      </div>
      {result.feedback && <p className="mt-2 leading-relaxed">{result.feedback}</p>}

      {result.missing_points.length > 0 && (
        <div className="mt-3">
          <div className="text-xs font-medium text-muted">Missing</div>
          <ul className="mt-1 list-inside list-disc space-y-0.5">
            {result.missing_points.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        </div>
      )}

      {kind === 'short' && (
        <div className="mt-3">
          <div className="text-xs font-medium text-muted">Reference answer</div>
          <p className="mt-1 leading-relaxed">{result.answer}</p>
        </div>
      )}

      {result.sources.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {result.sources.map((s) => (
            <a
              key={s.title}
              href={docUrl(s.source)}
              target="_blank"
              rel="noreferrer"
              className="rounded border border-line bg-card px-2 py-1 font-mono text-[11px] text-muted hover:text-ink"
            >
              {s.title}
            </a>
          ))}
        </div>
      )}
    </div>
  )
}
