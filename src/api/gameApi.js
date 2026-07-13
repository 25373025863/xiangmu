const baseUrl = '/api'

export class GameApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'GameApiError'
    this.status = status
  }
}

export async function getGameDetail(gameId, signal) {
  const response = await fetch(`${baseUrl}/games/${encodeURIComponent(gameId)}`, { signal })
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    throw new GameApiError(body?.detail || '暂时无法获取游戏详情', response.status)
  }
  if (!body?.success || !body.data) {
    throw new GameApiError('游戏详情数据格式错误', response.status)
  }
  return body.data
}
