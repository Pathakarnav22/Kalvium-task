import { useEffect, useMemo, useState } from 'react'
import { applyRecommendation, exportUrl, getFactualReports, getInstructionalReports, getLesson, getLessonEdit, saveLessonEdit, runFactualQC, runInstructionalQC } from '../services/review'

const SECTION_MAP: Record<string, { label: string; fields: { key: string; label: string }[] }> = {
  introduction: {
    label: 'Introduction',
    fields: [
      { key: 'duration_minutes', label: 'Estimated Duration' },
      { key: 'content', label: 'Explanation' },
      { key: 'why_it_matters', label: 'Why it Matters' },
      { key: 'real_world_context', label: 'Real World Context' },
    ]
  },
  core_concepts: {
    label: 'Core Concept',
    fields: [
      { key: 'title', label: 'Title' },
      { key: 'duration_minutes', label: 'Estimated Duration' },
      { key: 'explanation', label: 'Explanation' },
      { key: 'example', label: 'Example' },
    ]
  },
  step_by_step_examples: {
    label: 'Step-by-Step Example',
    fields: [
      { key: 'title', label: 'Title' },
      { key: 'duration_minutes', label: 'Estimated Duration' },
      { key: 'steps', label: 'Steps' },
    ]
  },
  real_world_applications: {
    label: 'Real World Applications',
    fields: [
      { key: 'duration_minutes', label: 'Estimated Duration' },
      { key: 'applications', label: 'Practical Applications' },
    ]
  },
  practical_activity: {
    label: 'Practical Activity',
    fields: [
      { key: 'completion_time_minutes', label: 'Estimated Duration' },
      { key: 'instructions', label: 'Activity' },
      { key: 'expected_outcomes', label: 'Expected Outcomes' },
    ]
  },
  knowledge_check: {
    label: 'Knowledge Check',
    fields: [
      { key: 'duration_minutes', label: 'Estimated Duration' },
      { key: 'questions', label: 'Questions' },
    ]
  },
  summary: {
    label: 'Summary',
    fields: [
      { key: 'duration_minutes', label: 'Estimated Duration' },
      { key: 'key_points', label: 'Key Takeaways' },
      { key: 'objective_reinforcement', label: 'Objective Reinforcement' },
    ]
  },
};

interface LessonSectionProps {
  sectionName: string;
  value: any;
  onChange: (newValue: any) => void;
}

function RenderObjectContent({ 
  obj, 
  sectionName, 
  index, 
  onChange 
}: { 
  obj: any; 
  sectionName: string; 
  index?: number; 
  onChange: (updatedObj: any) => void 
}) {
  const config = SECTION_MAP[sectionName];
  if (!config) return null;

  return (
    <div className={`mt-6 rounded-xl border bg-slate-50 p-4 ${index !== undefined ? 'border-slate-200' : ''}`}>
      <h3 className="mb-4 text-lg font-semibold text-slate-800 capitalize">
        {index !== undefined ? `${config.label} #${index + 1}` : config.label}
      </h3>
      <div className="grid gap-4">
        {config.fields.map(({ key, label }) => {
          const val = obj[key];
          if (val === undefined || val === null) return null;

          const displayValue = Array.isArray(val) 
            ? val.map(item => typeof item === 'object' ? JSON.stringify(item) : item).join('\n') 
            : String(val);

          return (
            <div key={key} className="flex flex-col">
              <label className="text-xs font-medium text-slate-500 uppercase">{label}</label>
              <textarea
                rows={displayValue.length > 100 ? 4 : 2}
                className="mt-1 w-full rounded border p-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                value={displayValue}
                onChange={(e) => {
                  onChange({ ...obj, [key]: e.target.value });
                }}
              />
            </div>
          );
        })}

        <div className="flex flex-col">
          <label className="text-xs font-medium text-yellow-600 uppercase">Instructor Recommendation</label>
          <textarea
            rows={2}
            className="mt-1 w-full rounded border p-2 text-sm outline-none focus:ring-2 focus:ring-yellow-500 bg-yellow-50 border-yellow-200"
            value={obj.instructor_recommendation || ''}
            onChange={(e) => onChange({ ...obj, instructor_recommendation: e.target.value })}
          />
        </div>
      </div>
    </div>
  );
}

function LessonSection({ sectionName, value, onChange }: LessonSectionProps) {
  if (Array.isArray(value)) {
    return (
      <>
        {value.map((item, idx) => (
          <RenderObjectContent 
            key={idx} 
            obj={item} 
            sectionName={sectionName} 
            index={idx} 
            onChange={(updatedItem) => {
              const newValue = [...value];
              newValue[idx] = updatedItem;
              onChange(newValue);
            }} 
          />
        ))}
      </>
    );
  }

  if (typeof value === 'object' && value !== null) {
    return <RenderObjectContent obj={value} sectionName={sectionName} onChange={onChange} />;
  }

  return (
    <div className="mt-6">
      <label className="block font-semibold text-slate-700 capitalize">{sectionName.replaceAll('_', ' ')}</label>
      <textarea
        rows={5}
        className="mt-2 w-full rounded-lg border p-3 font-mono text-sm focus:ring-2 focus:ring-blue-500 outline-none"
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
      />
      <div className="mt-2">
        <label className="text-xs font-medium text-yellow-600 uppercase">Instructor Recommendation</label>
        <textarea
          rows={2}
          className="mt-1 w-full rounded border p-2 text-sm outline-none focus:ring-2 focus:ring-yellow-500 bg-yellow-50 border-yellow-200"
          value={typeof value === 'object' ? value.instructor_recommendation : ''}
          onChange={(e) => {
            onChange({ content: value, instructor_recommendation: e.target.value });
          }}
        />
      </div>
    </div>
  );
}

function QCReport({ 
  title, 
  report, 
  onApply, 
  onRun, 
  isLoading, 
  type 
}: { 
  title: string; 
  report: any; 
  onApply: (issue: any, section: string) => void; 
  onRun: () => void; 
  isLoading: boolean; 
  type: 'factual' | 'instructional' 
}) {
  if (!report) {
    return (
      <div className="rounded-xl border border-dashed p-4 text-center text-sm text-slate-500">
        <h3 className="mb-2 font-semibold text-slate-700">{title}</h3>
        {isLoading ? (
          <div className="flex flex-col items-center gap-2">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
            <p>Executing AI agent...</p>
          </div>
        ) : (
          <>
            <p className="mb-4 text-slate-400">Report not generated yet</p>
            <button 
              onClick={onRun} 
              className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-700 transition-colors"
            >
              Run {type === 'factual' ? 'Factual' : 'Instructional'} QC
            </button>
          </>
        )}
      </div>
    );
  }

  if (report.status === 'failed') {
    return (
      <div className="rounded-xl border bg-red-50 p-4 shadow-sm">
        <div className="mb-2 flex items-center justify-between border-b border-red-100 pb-2">
          <h3 className="font-semibold text-red-800">{title}</h3>
          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-bold text-red-700">Failed</span>
        </div>
        <p className="text-sm text-red-600 leading-relaxed">{report.error_message || 'Unknown error occurred during QC execution.'}</p>
        <button 
          onClick={onRun} 
          className="mt-4 w-full rounded-lg bg-white border border-red-200 py-2 text-xs font-medium text-red-700 hover:bg-red-100 transition-colors"
        >
          Retry {type === 'factual' ? 'Factual' : 'Instructional'} QC
        </button>
      </div>
    );
  }

  const issues = report.issues || [];
  const counts = report.counts || {};

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-center justify-between border-b pb-3">
        <h3 className="font-semibold text-slate-800">{title}</h3>
        <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-bold text-blue-700">
          Score: {report.overall_score}
        </span>
      </div>
      
      <div className="mb-4 text-sm text-slate-600">
        <p className="font-medium">Summary:</p>
        <p className="mt-1 leading-relaxed">{report.summary}</p>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2 text-xs">
        {Object.entries(counts).map(([key, val]) => (
          <div key={key} className="rounded bg-slate-100 p-2 text-center">
            <span className="block font-medium text-slate-500 uppercase">{key.replaceAll('_', ' ')}</span>
            <span className="text-lg font-bold text-slate-800">{String(val)}</span>
          </div>
        ))}
      </div>

      <div className="space-y-3">
        <p className="text-xs font-semibold text-slate-500 uppercase">Issues ({issues.length})</p>
        {issues.map((issue: any) => (
          <div key={issue.issue_id} className="rounded border p-3 text-sm transition-colors hover:bg-slate-50">
            <div className="flex items-center justify-between mb-1">
              <strong className="text-xs font-mono text-slate-400">{issue.issue_id}</strong>
              <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                issue.severity === 'critical' ? 'bg-red-100 text-red-700' :
                issue.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                'bg-yellow-100 text-yellow-700'
              }`}>
                {issue.severity}
              </span>
            </div>
            <p className="mb-2 text-slate-700">{issue.explanation}</p>
            <button
              onClick={() => void onApply(issue, issue.lesson_section)}
              className="text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline"
            >
              Apply {type === 'factual' ? 'correction' : 'recommendation'} &rarr;
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function InstructorReview({ initialLessonId = '29' }: { initialLessonId?: string }) {
  const [lessonId, setLessonId] = useState(initialLessonId)
  const [lesson, setLesson] = useState<any>(null)
  const [content, setContent] = useState<any>({})
  const [factual, setFactual] = useState<any[]>([])
  const [instructional, setInstructional] = useState<any[]>([])
  const [message, setMessage] = useState('')
  const [loadingFactual, setLoadingFactual] = useState(false)
  const [loadingInstructional, setLoadingInstructional] = useState(false)

  async function load() {
    setMessage('')
    try {
      const loaded = await getLesson(Number(lessonId)); setLesson(loaded)
      const edit = await getLessonEdit(Number(lessonId)); setContent(edit ? edit.content : loaded.content)
      
      const fReports = await getFactualReports(Number(lessonId)); setFactual([...fReports].sort((a, b) => {
        if (a.status === 'completed' && b.status !== 'completed') return -1
        if (b.status === 'completed' && a.status !== 'completed') return 1
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      }))
      const iReports = await getInstructionalReports(Number(lessonId)); setInstructional([...iReports].sort((a, b) => {
        if (a.status === 'completed' && b.status !== 'completed') return -1
        if (b.status === 'completed' && a.status !== 'completed') return 1
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      }))
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Unable to load review') }
  }
  useEffect(() => { void load() }, [])
  
  const sections = useMemo(() => Object.keys(content ?? {}).filter((key) => key !== 'lesson_overview'), [content])

  async function save() { try { await saveLessonEdit(Number(lessonId), content, 'Instructor review save'); setMessage('Edits saved') } catch (error) { setMessage(error instanceof Error ? error.message : 'Save failed') } }
  
  async function apply(source: 'factual' | 'instructional', issue: any, section: string) {
    const replacement = issue.suggested_correction || issue.recommendation || 'Apply reviewer-approved improvement'
    try { 
      await applyRecommendation(Number(lessonId), { source_qc: source, issue_id: issue.issue_id, section, replacement }); 
      setContent((current: any) => {
        const sectionVal = current[section];
        if (typeof sectionVal === 'object' && sectionVal !== null && !Array.isArray(sectionVal)) {
          return { ...current, [section]: { ...sectionVal, instructor_recommendation: replacement } };
        }
        if (Array.isArray(sectionVal)) {
          return { ...current, [section]: { ...sectionVal, instructor_recommendation: replacement } };
        }
        return { ...current, [section]: { content: sectionVal, instructor_recommendation: replacement } };
      }); 
      setMessage('Recommendation applied') 
    }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Unable to apply recommendation') }
  }

  async function runFactual() {
    setLoadingFactual(true)
    setMessage('')
    try {
      const report = await runFactualQC(Number(lessonId))
      const updatedReports = [report, ...factual]
      setFactual(updatedReports)
      setMessage('Factual QC completed')
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Factual QC failed') }
    finally { setLoadingFactual(false) }
  }

  async function runInstructional() {
    setLoadingInstructional(true)
    setMessage('')
    try {
      const report = await runInstructionalQC(Number(lessonId))
      const updatedReports = [report, ...instructional]
      setInstructional(updatedReports)
      setMessage('Instructional QC completed')
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Instructional QC failed') }
    finally { setLoadingInstructional(false) }
  }

  return (
    <section className="p-6 lg:p-10 max-w-7xl mx-auto">
      <div className="mb-8 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 rounded-lg border bg-white px-3 py-2">
          <span className="text-xs font-medium text-slate-400 uppercase">Lesson ID</span>
          <input 
            className="w-20 outline-none text-sm font-mono" 
            value={lessonId} 
            onChange={(e) => setLessonId(e.target.value)} 
            type="number" 
          />
        </div>
        <button className="rounded-lg border bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50 transition-colors" onClick={() => void load()}>Load</button>
        <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors shadow-sm" onClick={() => void save()}>Save Edits</button>
        <a className="rounded-lg border bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50 transition-colors" href={exportUrl(Number(lessonId))}>Export Markdown</a>
      </div>

      {message && (
        <div className="mb-6 rounded-lg bg-blue-50 p-3 text-sm text-blue-700 border border-blue-100 animate-in fade-in slide-in-from-top-1">
          {message}
        </div>
      )}

      <div className="grid gap-8 xl:grid-cols-[2fr_1fr]">
        <div className="rounded-2xl border bg-white p-6 shadow-sm">
          <div className="mb-8 border-b pb-6">
            <h2 className="text-3xl font-bold text-slate-900">{lesson?.lesson_title ?? 'Lesson Review'}</h2>
            <p className="mt-2 text-slate-600 italic">Objective: {lesson?.learning_objective ?? 'No objective provided'}</p>
          </div>
          
          <div className="space-y-4">
            {sections.map((section) => (
              <LessonSection 
                key={section} 
                sectionName={section} 
                value={content[section]} 
                onChange={(newValue) => setContent((current: any) => ({ ...current, [section]: newValue }))} 
              />
            ))}
          </div>
        </div>

        <aside className="space-y-6">
          <QCReport 
            title="QC Agent 1 (Factual)" 
            report={factual[0]} 
            type="factual"
            onApply={(issue, section) => void apply('factual', issue, section)} 
            onRun={runFactual}
            isLoading={loadingFactual}
          />
          <QCReport 
            title="QC Agent 2 (Instructional)" 
            report={instructional[0]} 
            type="instructional"
            onApply={(issue, section) => void apply('instructional', issue, section)} 
            onRun={runInstructional}
            isLoading={loadingInstructional}
          />
        </aside>
      </div>
    </section>
  )
}
