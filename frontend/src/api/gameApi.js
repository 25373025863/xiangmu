import { apiRequest } from './request.js'

export function getGames(filters = {}) {
  const query = new URLSearchParams(
    Object.entries(filters).filter(([, value]) => value)
  )
  return apiRequest(`/api/games?${query}`)
}

export function getGame(gameId) {
  return apiRequest(`/api/games/${encodeURIComponent(gameId)}`)
}
