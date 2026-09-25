const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api'

export const apiRequest = async <T,>(path: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) throw new Error(`API request failed: ${response.status}`)
  return response.status === 204 ? ({} as T) : response.json() as Promise<T>
}
