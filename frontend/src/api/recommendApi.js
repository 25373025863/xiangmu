import { apiRequest } from './request.js'
import { normalizeProviderConfig } from '../utils/providerConfig.js'

export function submitPreferences(preferences) {
  return apiRequest('/api/preferences/submit', {
    method: 'POST',
    body: JSON.stringify(preferences)
  })
}

export function getRecommendations(preferences, providerConfig = {}) {
  const { apiKey, apiBaseUrl, model } = normalizeProviderConfig(providerConfig)
  const body = { preferences, limit: 5 }
  if (apiBaseUrl) body.apiBaseUrl = apiBaseUrl
  if (model) body.model = model

  return apiRequest('/api/recommend', {
    method: 'POST',
    headers: apiKey ? { 'x-ai-api-key': apiKey } : {},
    body: JSON.stringify(body)
  })
}

export function readSteamProfile(steamIdentifier) {
  return apiRequest('/api/steam/profile', {
    method: 'POST',
    body: JSON.stringify({ steam_identifier: steamIdentifier })
  })
}
