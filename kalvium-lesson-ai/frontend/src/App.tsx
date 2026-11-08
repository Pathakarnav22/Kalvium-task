import { BookOpen, LayoutDashboard, PlusCircle, Settings, Sparkles, ClipboardCheck, PencilLine } from 'lucide-react'
import { useBackendHealth } from './hooks/useBackendHealth'
import Dashboard from './pages/Dashboard'
import InstructionalQuality from './pages/InstructionalQuality'
import InstructorReview from './pages/InstructorReview'
import CreateLesson from './pages/CreateLesson'
import SavedLessons from './pages/SavedLessons'
import { useState } from 'react'

const navigation = [
	{ id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
	{ id: 'create', label: 'Create Lesson', icon: PlusCircle },
	{ id: 'saved', label: 'Saved Lessons', icon: BookOpen },
	{ id: 'settings', label: 'Settings', icon: Settings },
	{ id: 'instructional-qc', label: 'Instructional Quality', icon: ClipboardCheck },
	{ id: 'review', label: 'Instructor Review', icon: PencilLine },
]

export default function App() {
	const [activePage, setActivePage] = useState('dashboard')
	const [selectedLessonId, setSelectedLessonId] = useState(29)
	const { status, checkConnection } = useBackendHealth()
	const activeLabel = navigation.find((item) => item.id === activePage)?.label ?? 'Dashboard'
	const statusClass = status === 'connected' ? 'bg-emerald-500' : status === 'checking' ? 'bg-amber-400' : 'bg-red-500'

	return (
		<div className="min-h-screen bg-[#f5f7fb] lg:grid lg:grid-cols-[248px_1fr]">
			<aside className="bg-[#111827] text-white lg:min-h-screen">
				<div className="flex h-20 items-center gap-3 border-b border-white/10 px-6">
					<div className="grid h-10 w-10 place-items-center rounded-xl bg-blue-600"><Sparkles size={20} /></div>
					<div><p className="font-semibold leading-tight">Kalvium</p><p className="text-xs text-slate-400">Lesson AI</p></div>
				</div>
				<nav className="flex gap-2 overflow-x-auto p-4 lg:block lg:space-y-2">
					{navigation.map(({ id, label, icon: Icon }) => (
						<button key={id} onClick={() => setActivePage(id)} className={`flex shrink-0 items-center gap-3 rounded-lg px-4 py-3 text-sm transition ${activePage === id ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-white/5'}`}>
							<Icon size={18} /> {label}
						</button>
					))}
				</nav>
			</aside>
			<main className="min-w-0">
				<header className="flex h-20 items-center justify-between border-b border-slate-200 bg-white px-6 lg:px-10">
					<h1 className="text-lg font-semibold text-slate-900">{activeLabel}</h1>
					<button onClick={() => void checkConnection()} className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm" title="Retry backend health check">
						<span className={`h-2 w-2 rounded-full ${statusClass}`} />
						{status === 'connected' ? 'Backend connected' : status === 'checking' ? 'Checking backend' : 'Backend disconnected'}
					</button>
				</header>
				{activePage === 'dashboard' ? <Dashboard onNavigate={setActivePage} /> : activePage === 'create' ? <CreateLesson /> : activePage === 'saved' ? <SavedLessons onOpen={(lessonId) => { setSelectedLessonId(lessonId); setActivePage('review') }} /> : activePage === 'instructional-qc' ? <InstructionalQuality /> : activePage === 'review' ? <InstructorReview initialLessonId={String(selectedLessonId)} /> : (
					<section className="p-6 lg:p-10"><div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm"><h2 className="text-xl font-semibold">{activeLabel}</h2><p className="mt-2 text-sm text-slate-500">This workspace is ready for Phase 2 implementation.</p></div></section>
				)}
			</main>
		</div>
	)
}
