import { useEffect, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { api } from '../api'
import type { Course, Progress } from '../types'
import { COLOR } from '../courses'
import { Card, CoursePicker, CourseTag, ErrorNote, PageTitle, Thinking } from '../components/ui'

const pct = (v: number) => `${Math.round(v * 100)}%`

// "Shortest paths (Dijkstra, Bellman-Ford, ...)" -> "Shortest paths"
function shortName(name: string): string {
  const cut = name.split(/[,(:]/)[0].trim()
  return cut.length > 26 ? cut.slice(0, 25) + '…' : cut
}

export default function ProgressPage() {
  const [course, setCourse] = useState<Course | null>(null)
  const [data, setData] = useState<Progress | null>(null)
  const [error, setError] = useState<string>()

  useEffect(() => {
    api.progress(course ?? undefined).then(setData, (e) => setError(e.message))
  }, [course])

  if (error) return <ErrorNote message={error} />
  if (!data) return <Thinking label="Loading" />

  const answered = data.daily.reduce((s, d) => s + d.answered, 0)
  const spent = data.spend.reduce((s, r) => s + Number(r.usd), 0)
  const chat = data.spend.find((s) => s.kind === 'chat')

  return (
    <div>
      <div className="flex items-start justify-between">
        <PageTitle title="Progress" sub="Mastery weights recent answers more: a week-old attempt counts about a third." />
        <div className="pt-1">
          <CoursePicker value={course} onChange={setCourse} allowAll />
        </div>
      </div>

      <div className="mb-4 grid grid-cols-3 gap-4">
        <Kpi label="answered, last 14 days" value={String(answered)} />
        <Kpi label="API spend, last 7 days" value={`$${spent.toFixed(2)}`} />
        <Kpi label="chat cache hit rate" value={chat?.cache_hit != null ? pct(chat.cache_hit) : '–'} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
        <Card className="px-5 py-4">
          <h2 className="mb-3 text-sm font-medium">Mastery by topic</h2>
          <ResponsiveContainer width="100%" height={Math.max(220, data.mastery.length * 26)}>
            <BarChart data={data.mastery.map((t) => ({ ...t, label: shortName(t.name) }))} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid horizontal={false} stroke="#e5dfd2" />
              <XAxis type="number" domain={[0, 1]} tickFormatter={pct} tick={{ fontSize: 11, fill: '#6b6f7b' }} />
              <YAxis type="category" dataKey="label" width={170} interval={0} tick={AxisLabel} />
              <Tooltip
                formatter={(v) => [pct(Number(v)), 'mastery']}
                labelFormatter={(_, items) => items?.[0]?.payload?.name ?? ''}
                cursor={{ fill: 'rgb(31 42 68 / 0.04)' }}
              />
              <Bar dataKey="mastery" radius={[0, 4, 4, 0]} barSize={12}>
                {data.mastery.map((t) => (
                  <Cell key={t.id} fill={COLOR[t.course_id]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <div className="space-y-4">
          <Card className="px-5 py-4">
            <h2 className="mb-3 text-sm font-medium">Work on these next</h2>
            <ol className="space-y-3">
              {data.weakest.map((t, i) => (
                <li key={t.id} className="flex items-start gap-3 text-sm">
                  <span className="font-serif text-lg leading-5 text-muted">{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <div className="leading-5">{t.name}</div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted">
                      <CourseTag course={t.course_id} />
                      {t.attempts === 0 ? 'not tested yet' : `${pct(t.mastery)} · ${t.attempts} tries`}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </Card>

          <Card className="px-5 py-4">
            <h2 className="mb-2 text-sm font-medium">Spend by feature</h2>
            <table className="w-full text-xs">
              <tbody>
                {data.spend.map((s) => (
                  <tr key={s.kind} className="border-b border-line/60 last:border-0">
                    <td className="py-1.5 font-mono">{s.kind}</td>
                    <td className="py-1.5 text-right text-muted">{s.calls} calls</td>
                    <td className="py-1.5 text-right font-mono">${Number(s.usd).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      </div>

      <Card className="mt-4 px-5 py-4">
        <h2 className="mb-3 text-sm font-medium">Daily accuracy</h2>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data.daily} margin={{ left: -12, right: 12 }}>
            <CartesianGrid vertical={false} stroke="#e5dfd2" />
            <XAxis dataKey="day" tickFormatter={(d) => d.slice(5)} tick={{ fontSize: 11, fill: '#6b6f7b' }} />
            <YAxis domain={[0, 1]} tickFormatter={pct} tick={{ fontSize: 11, fill: '#6b6f7b' }} />
            <Tooltip formatter={(v, name) => (name === 'accuracy' ? pct(Number(v)) : v)} />
            <Line type="monotone" dataKey="accuracy" stroke="#1f2a44" strokeWidth={2} dot={{ r: 3 }} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  )
}

// recharts wraps long tick labels onto two lines; keep them on one
function AxisLabel({ x, y, payload }: { x?: number | string; y?: number | string; payload?: { value: string } }) {
  return (
    <text x={Number(x) - 6} y={Number(y)} dy={4} textAnchor="end" fontSize={11} fill="#1f2a44">
      {payload?.value}
    </text>
  )
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <Card className="px-5 py-4">
      <div className="font-serif text-3xl font-semibold">{value}</div>
      <div className="mt-1 text-xs text-muted">{label}</div>
    </Card>
  )
}
