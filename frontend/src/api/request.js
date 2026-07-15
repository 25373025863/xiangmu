export async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  })

  let payload
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    const message = payload?.detail || payload?.message || `请求失败 (${response.status})`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}
