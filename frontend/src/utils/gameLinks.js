export function safeWebUrl(value) {
  if (!value) return ''
  try {
    const url = new URL(String(value), window.location.origin)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : ''
  } catch {
    return ''
  }
}

export function isSteamSource(source) {
  return String(source || '').toLowerCase().includes('steam')
}

export function steamAppId(game = {}) {
  const directId = Number(game.steam_app_id)
  if (Number.isInteger(directId) && directId > 0) return directId
  const rawId = String(game.id ?? game.game_id ?? '')
  const match = rawId.match(/^steam-(\d+)$/i)
  return match ? Number(match[1]) : null
}

export function isRemoteSteamGame(game = {}) {
  return isSteamSource(game.source) || /^steam-\d+$/i.test(String(game.id ?? game.game_id ?? ''))
}

export function steamStoreUrl(value, title, appId = null) {
  const candidate = safeWebUrl(value)
  if (candidate) {
    const hostname = new URL(candidate).hostname.toLowerCase()
    if (hostname === 'store.steampowered.com' || hostname.endsWith('.store.steampowered.com')) {
      return candidate
    }
  }
  const numericAppId = Number(appId)
  if (Number.isInteger(numericAppId) && numericAppId > 0) {
    return `https://store.steampowered.com/app/${numericAppId}/`
  }
  return `https://store.steampowered.com/search/?term=${encodeURIComponent(title)}`
}
