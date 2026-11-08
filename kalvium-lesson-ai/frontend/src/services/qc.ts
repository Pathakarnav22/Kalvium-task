const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export async function runInstructionalQC(lessonId: number) {
  const response = await fetch(`${API_BASE_URL}/lessons/${lessonId}/qc/instructional`, { method: 'POST' })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? 'Instructional QC failed')
  return body
}

export async function getInstructionalQCHistory(lessonId: number) {
  const response = await fetch(`${API_BASE_URL}/lessons/${lessonId}/qc/instructional`)
  if (!response.ok) throw new Error('Unable to load instructional QC history')
  return response.json()
}
