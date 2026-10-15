const API_BASE = (import.meta.env.VITE_API_URL ?? '/api/v1').replace(/\/+$/, '')
const API_ROOT = API_BASE.replace(/\/v1$/, '')
const AUTH_TOKEN_KEY = 'draftflow_access_token'

export const setAuthToken = (token: string | null, remember = false) => {
  if (token) {
    window.localStorage.removeItem(AUTH_TOKEN_KEY)
    window.sessionStorage.removeItem(AUTH_TOKEN_KEY)
    if (remember) {
      window.localStorage.setItem(AUTH_TOKEN_KEY, token)
    } else {
      window.sessionStorage.setItem(AUTH_TOKEN_KEY, token)
    }
  } else {
    window.localStorage.removeItem(AUTH_TOKEN_KEY)
    window.sessionStorage.removeItem(AUTH_TOKEN_KEY)
  }
}

export const getAuthToken = (): string | null =>
  window.localStorage.getItem(AUTH_TOKEN_KEY) ?? window.sessionStorage.getItem(AUTH_TOKEN_KEY)

const request = async <T,>(base: string, path: string, options?: RequestInit): Promise<T> => {
  const headers = new Headers(options?.headers)
  headers.set('Content-Type', 'application/json')
  const token = getAuthToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${base}${path}`, {
    ...options,
    headers,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(error?.detail ?? `API request failed: ${response.status}`)
  }
  return response.status === 204 ? ({} as T) : response.json() as Promise<T>
}

export const apiRequest = <T,>(path: string, options?: RequestInit): Promise<T> =>
  request(API_BASE, path, options)

export const legacyApiRequest = <T,>(path: string, options?: RequestInit): Promise<T> =>
  request(API_ROOT, path, options)
