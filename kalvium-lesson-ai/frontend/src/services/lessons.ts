const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export async function generateLesson(payload: { lesson_title: string; learning_objective: string }) {
  const response = await fetch(`${API_BASE_URL}/lessons/generate`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Lesson generation failed')
  return body
}

export async function listLessons() {
  const response = await fetch(`${API_BASE_URL}/lessons`)
  if (!response.ok) throw new Error('Unable to load saved lessons')
  return response.json()
}
