const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  const contentType = res.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await res.json() : { detail: await res.text() }

  if (!res.ok && !data.ok) {
    const msg = data.detail || data.erro || `Erro HTTP ${res.status}`
    throw new Error(msg)
  }

  return data
}

export function apiPost(path, body) {
  return apiFetch(path, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function apiPatch(path, body) {
  return apiFetch(path, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function apiDelete(path) {
  return apiFetch(path, { method: 'DELETE' })
}
