import { useState } from 'react'
import { generateLesson } from '../services/lessons'

export default function CreateLesson() {
  const [title, setTitle] = useState('')
  const [objective, setObjective] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try { setResult(await generateLesson({ lesson_title: title, learning_objective: objective })) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Lesson generation failed') }
    finally { setLoading(false) }
  }

  return <section className="p-6 lg:p-10"><div className="mx-auto max-w-3xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-semibold">Create a lesson</h2><p className="mt-1 text-sm text-slate-500">Research, generate, and save a lesson in under 45 minutes.</p><form className="mt-6 space-y-4" onSubmit={submit}><label className="block"><span className="text-sm font-medium">Lesson title</span><input required maxLength={200} value={title} onChange={(event) => setTitle(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2" placeholder="HTTP Requests and Responses" /></label><label className="block"><span className="text-sm font-medium">Learning objective</span><textarea required maxLength={1000} rows={4} value={objective} onChange={(event) => setObjective(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2" placeholder="Explain the learning outcome for students" /></label><button disabled={loading || !title.trim() || !objective.trim()} className="rounded-lg bg-blue-600 px-5 py-2.5 font-medium text-white disabled:opacity-60">{loading ? 'Researching and generating…' : 'Generate Lesson'}</button></form>{error && <p className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>} {result && <div className="mt-5 rounded-lg border border-emerald-200 bg-emerald-50 p-4"><strong>Lesson #{result.id}</strong> saved as {result.status}.<pre className="mt-3 max-h-80 overflow-auto rounded bg-white p-3 text-xs">{JSON.stringify(result.content, null, 2)}</pre></div>}</div></section>
}
