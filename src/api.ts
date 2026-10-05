const API_BASE = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1').replace(/\/+$/, '')
const AUTH_TOKEN_KEY = 'draftflow_access_token'

export const setAuthToken = (token: string | null) => {
  if (token) {
    sessionStorage.setItem(AUTH_TOKEN_KEY, token)
  } else {
    sessionStorage.removeItem(AUTH_TOKEN_KEY)
  }
}

export const apiRequest = async <T,>(path: string, options?: RequestInit): Promise<T> => {
  const headers = new Headers(options?.headers)
  headers.set('Content-Type', 'application/json')
  const token = sessionStorage.getItem(AUTH_TOKEN_KEY)
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(error?.detail ?? `API request failed: ${response.status}`)
  }
  return response.status === 204 ? ({} as T) : response.json() as Promise<T>
}
