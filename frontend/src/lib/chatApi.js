const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const CHAT_ENDPOINTS = ['/api/v1/chat/query', '/perguntar']

async function readJson(res) {
  const ct = res.headers.get('content-type') || ''
  if (!ct.includes('application/json')) {
    return { detail: await res.text() }
  }
  return res.json()
}

export async function sendQuestion(texto) {
  let lastError = null

  for (const endpoint of CHAT_ENDPOINTS) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ texto }),
      })

      const data = await readJson(res)
      if (res.status === 404) {
        lastError = new Error(`Endpoint indisponivel: ${endpoint}`)
        continue
      }
      if (!res.ok) {
        throw new Error(data.detail || data.erro || `Erro HTTP ${res.status}`)
      }
      return data
    } catch (err) {
      lastError = err
    }
  }

  throw lastError || new Error('Nenhum endpoint de chat disponivel.')
}

export async function sendPdf(file, prompt) {
  const form = new FormData()
  form.append('file', file)
  if (prompt) form.append('prompt', prompt)

  const res = await fetch(`${API_BASE}/resumir_pdf`, {
    method: 'POST',
    credentials: 'include',
    body: form,
  })

  const data = await readJson(res)
  if (!res.ok) {
    throw new Error(data.detail || 'Erro ao processar PDF')
  }
  return data
}

export async function sendVideoUrl(link) {
  const res = await fetch(`${API_BASE}/resumir_video`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ link }),
  })

  const data = await readJson(res)
  if (!res.ok) {
    throw new Error(data.detail || 'Erro ao resumir video')
  }
  return data
}

export async function checkHealth() {
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5000)
    const res = await fetch(`${API_BASE}/health`, { signal: controller.signal })
    clearTimeout(timeout)
    return res.ok
  } catch {
    return false
  }
}
