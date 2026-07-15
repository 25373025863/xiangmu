const SESSION_CONFIG_KEY = 'aiProviderConfig'
const LEGACY_API_KEY_KEYS = ['userApiKey', 'member4_ai_api_key']

export function normalizeProviderConfig(value = {}) {
  const source = typeof value === 'string' ? { apiKey: value } : (value || {})
  return {
    apiKey: String(source.apiKey || '').trim(),
    apiBaseUrl: String(source.apiBaseUrl || '').trim(),
    model: String(source.model || '').trim()
  }
}

function getSessionStorage() {
  try {
    return window.sessionStorage
  } catch {
    return null
  }
}

export function readProviderConfig() {
  const storage = getSessionStorage()
  if (!storage) return normalizeProviderConfig()

  let storedConfig = {}
  try {
    const rawConfig = storage.getItem(SESSION_CONFIG_KEY)
    const parsedConfig = rawConfig ? JSON.parse(rawConfig) : {}
    if (parsedConfig && typeof parsedConfig === 'object' && !Array.isArray(parsedConfig)) {
      storedConfig = parsedConfig
    }
  } catch {
    storedConfig = {}
  }

  let legacyApiKey = ''
  for (const key of LEGACY_API_KEY_KEYS) {
    try {
      legacyApiKey ||= storage.getItem(key) || ''
    } catch {
      break
    }
  }

  const config = normalizeProviderConfig({
    ...storedConfig,
    apiKey: storedConfig.apiKey || legacyApiKey
  })

  if (legacyApiKey) {
    try {
      storage.setItem(SESSION_CONFIG_KEY, JSON.stringify(config))
      LEGACY_API_KEY_KEYS.forEach(key => storage.removeItem(key))
    } catch {
      return config
    }
  }

  return config
}

export function saveProviderConfig(value) {
  const storage = getSessionStorage()
  if (!storage) throw new Error('当前浏览器无法使用会话存储，请检查隐私设置。')

  const config = normalizeProviderConfig(value)
  storage.setItem(SESSION_CONFIG_KEY, JSON.stringify(config))
  LEGACY_API_KEY_KEYS.forEach(key => storage.removeItem(key))
  return config
}

export function clearProviderConfig() {
  const storage = getSessionStorage()
  if (!storage) return
  storage.removeItem(SESSION_CONFIG_KEY)
  LEGACY_API_KEY_KEYS.forEach(key => storage.removeItem(key))
}
