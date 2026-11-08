import { useCallback, useEffect, useState } from 'react'
import { getHealth } from '../services/api'

export type ConnectionStatus = 'checking' | 'connected' | 'disconnected'

export function useBackendHealth() {
  const [status, setStatus] = useState<ConnectionStatus>('checking')
  const checkConnection = useCallback(async () => {
    setStatus('checking')
    try {
      const result = await getHealth()
      setStatus(result.status === 'healthy' ? 'connected' : 'disconnected')
    } catch {
      setStatus('disconnected')
    }
  }, [])

  useEffect(() => { void checkConnection() }, [checkConnection])
  return { status, checkConnection }
}
