import { useEffect, useState } from 'react'
import { listLessons } from '../services/lessons'

export default function SavedLessons({ onOpen }: { onOpen?: (lessonId: number) => void }) {
  const [lessons, setLessons] = useState<any[]>([])
  const [error, setError] = useState('')
  async function load() { try { setLessons(await listLessons()); setError('') } catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to load lessons') } }
  useEffect(() => { void load() }, [])
  return <section className="p-6 lg:p-10"><div className="flex items-center justify-between"><div><h2 className="text-xl font-semibold">Saved Lessons</h2><p className="mt-1 text-sm text-slate-500">Generated and reviewed lessons stored in SQLite.</p></div><button className="rounded-lg border px-4 py-2" onClick={() => void load()}>Refresh</button></div>{error && <p className="mt-4 text-sm text-red-600">{error}</p>}<div className="mt-6 grid gap-4 md:grid-cols-2">{lessons.map((lesson) => <article key={lesson.id} className="rounded-xl border border-slate-200 bg-white p-5"><div className="flex items-start justify-between gap-3"><h3 className="font-semibold">{lesson.lesson_title}</h3><span className="rounded-full bg-slate-100 px-2 py-1 text-xs">#{lesson.id}</span></div><p className="mt-2 text-sm text-slate-600">{lesson.learning_objective}</p><div className="mt-4 flex items-center justify-between"><p className="text-xs text-slate-400">{lesson.status} · {lesson.provider}</p><button className="rounded-lg border border-blue-200 px-3 py-1.5 text-sm text-blue-700" onClick={() => onOpen?.(lesson.id)}>Open in Review</button></div></article>)}</div>{!error && lessons.length === 0 && <p className="mt-6 rounded-lg border bg-white p-5 text-sm text-slate-500">No lessons saved yet.</p>}</section>
}
