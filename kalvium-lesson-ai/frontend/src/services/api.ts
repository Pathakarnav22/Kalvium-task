export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export type HealthResponse = { status: 'healthy' }

export async function getHealth(): Promise<HealthResponse> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 5000)
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { signal: controller.signal })
    if (!response.ok) throw new Error(`Health check failed: ${response.status}`)
    return await response.json() as HealthResponse
  } finally {
    window.clearTimeout(timeoutId)
  }
}
