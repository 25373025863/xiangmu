import { apiRequest } from './request.js'

export function getFavorites(page = 1, size = 20) {
  return apiRequest(`/api/favorites?page=${page}&size=${size}`)
}

export function addFavorite(gameId) {
  return apiRequest('/api/favorites', {
    method: 'POST',
    body: JSON.stringify({ game_id: gameId })
  })
}

export function removeFavorite(gameId) {
  return apiRequest(`/api/favorites/${encodeURIComponent(gameId)}`, {
    method: 'DELETE'
  })
}

export function getHistories(page = 1, size = 20) {
  return apiRequest(`/api/histories?page=${page}&size=${size}`)
}
