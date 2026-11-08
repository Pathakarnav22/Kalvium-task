import { Clock3, FileText, PlusCircle } from 'lucide-react'

export default function Dashboard({ onNavigate }: { onNavigate: (page: string) => void }) {
  return (
    <section className="p-6 lg:p-10">
      <div className="mb-8 rounded-2xl bg-gradient-to-r from-blue-700 to-blue-500 p-7 text-white shadow-sm">
        <p className="text-sm font-medium text-blue-100">Welcome to Kalvium Lesson AI</p>
        <h2 className="mt-2 text-3xl font-semibold">Create better lessons, faster.</h2>
        <p className="mt-3 max-w-xl text-sm text-blue-100">Plan engaging, research-backed lessons in one streamlined workspace.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <article onClick={() => onNavigate('create')} className="cursor-pointer rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-blue-300">
          <PlusCircle className="text-blue-600" />
          <h3 className="mt-4 font-semibold">Create a lesson</h3>
          <p className="mt-2 text-sm text-slate-500">Start from a title and learning objective.</p>
        </article>
        <article onClick={() => onNavigate('saved')} className="cursor-pointer rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-blue-300">
          <FileText className="text-violet-600" />
          <h3 className="mt-4 font-semibold">Saved lessons</h3>
          <p className="mt-2 text-sm text-slate-500">Review and manage your lesson drafts.</p>
        </article>
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <Clock3 className="text-emerald-600" />
          <h3 className="mt-4 font-semibold">45-minute planning</h3>
          <p className="mt-2 text-sm text-slate-500">Designed for focused classroom sessions.</p>
        </article>
      </div>
    </section>
  )
}
