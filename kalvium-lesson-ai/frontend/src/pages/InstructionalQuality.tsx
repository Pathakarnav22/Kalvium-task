import { useEffect, useState } from 'react'
import { getInstructionalQCHistory, runInstructionalQC } from '../services/qc'

export default function InstructionalQuality() {
  const [lessonId, setLessonId] = useState('29')
  const [history, setHistory] = useState<any[]>([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  async function loadHistory() {
    try { setHistory(await getInstructionalQCHistory(Number(lessonId))) } catch (error) { setMessage(error instanceof Error ? error.message : 'Unable to load reports') }
  }

  useEffect(() => { void loadHistory() }, [])

  async function run() {
    setLoading(true)
    setMessage('')
    try { const report = await runInstructionalQC(Number(lessonId)); setHistory((current) => [report, ...current]); setMessage(`QC completed with score ${report.overall_score}`) }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Instructional QC failed') }
    finally { setLoading(false) }
  }

  return <section className="p-6 lg:p-10"><div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap items-center gap-3"><div><h2 className="text-xl font-semibold">Instructional Quality</h2><p className="mt-1 text-sm text-slate-500">Independent evaluation of alignment, clarity, pacing, activities, and knowledge checks.</p></div><div className="ml-auto flex gap-2"><input value={lessonId} onChange={(event) => setLessonId(event.target.value)} type="number" min="1" aria-label="Lesson ID" className="w-24 rounded-lg border border-slate-300 px-3 py-2 text-sm"/><button onClick={() => void loadHistory()} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">History</button><button onClick={() => void run()} disabled={loading} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60">{loading ? 'Running…' : 'Run QC 2'}</button></div></div>{message && <p className="mt-4 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">{message}</p>}<div className="mt-6 space-y-3">{history.map((report) => <article key={report.id} className="rounded-lg border border-slate-200 p-4"><div className="flex justify-between"><strong>Report #{report.id}</strong><span className="font-semibold text-blue-700">{report.overall_score}/100</span></div><p className="mt-2 text-sm text-slate-600">{report.summary}</p><p className="mt-2 text-xs text-slate-400">{report.status} · {report.counts?.issues_identified ?? 0} issues</p></article>)}</div></div></section>
}
