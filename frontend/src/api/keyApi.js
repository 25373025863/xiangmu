import { apiRequest } from './request.js'
import { normalizeProviderConfig } from '../utils/providerConfig.js'

export function checkApiKey(providerConfig) {
  const { apiKey, apiBaseUrl, model } = normalizeProviderConfig(providerConfig)
  const body = {}
  if (apiBaseUrl) body.apiBaseUrl = apiBaseUrl
  if (model) body.model = model

  return apiRequest('/api/key/check', {
    method: 'POST',
    headers: apiKey ? { 'x-ai-api-key': apiKey } : {},
    body: JSON.stringify(body)
  })
}

export function checkConfig() {
  return apiRequest('/api/config/check')
}
