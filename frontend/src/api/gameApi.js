const API_BASE_URL = '/api'

export class GameApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'GameApiError'
    this.status = status
  }
}

export async function getGameDetail(gameId, signal) {
  const response = await fetch(
    `${API_BASE_URL}/games/${encodeURIComponent(gameId)}`,
    { signal }
  )
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    throw new GameApiError(body?.message || '暂时无法获取游戏详情', response.status)
  }
  if (body?.code !== 0 || !body.data) {
    throw new GameApiError(body?.message || '游戏详情数据格式错误', response.status)
  }
  return body.data
}
