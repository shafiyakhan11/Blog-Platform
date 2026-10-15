const configuredApiBase = import.meta.env.VITE_API_URL?.trim().replace(/\/+$/, '')
const API_BASE = !configuredApiBase
  ? '/api/v1'
  : configuredApiBase.endsWith('/api/v1')
    ? configuredApiBase
    : configuredApiBase.endsWith('/api')
      ? `${configuredApiBase}/v1`
      : `${configuredApiBase}/api/v1`
const API_ROOT = API_BASE.replace(/\/v1$/, '')
const AUTH_TOKEN_KEY = 'draftflow_access_token'

export class ApiRequestError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiRequestError'
    this.status = status
  }
}

export const getAuthRequestErrorMessage = (error: unknown, fallback: string): string => {
  if (!(error instanceof Error)) return fallback
  if (error.message.trim().toLowerCase() === 'not found') {
    return 'The account service was not found. Confirm the latest backend is deployed and VITE_API_URL points to its API origin.'
  }
  return error.message || fallback
}

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
    throw new ApiRequestError(error?.detail ?? `API request failed: ${response.status}`, response.status)
  }
  return response.status === 204 ? ({} as T) : response.json() as Promise<T>
}

export const apiRequest = <T,>(path: string, options?: RequestInit): Promise<T> =>
  request(API_BASE, path, options)

export const legacyApiRequest = <T,>(path: string, options?: RequestInit): Promise<T> =>
  request(API_ROOT, path, options)
