const fs = require('node:fs/promises')
const path = require('node:path')

const GAMES_FILE = path.join(__dirname, '..', 'data', 'games.json')

class GameNotFoundError extends Error {
  constructor(gameId) {
    super(`游戏不存在: ${gameId}`)
    this.name = 'GameNotFoundError'
  }
}

class GameDataError extends Error {
  constructor(message = '游戏数据暂时不可用') {
    super(message)
    this.name = 'GameDataError'
  }
}

async function readGames() {
  try {
    const source = await fs.readFile(GAMES_FILE, 'utf8')
    const games = JSON.parse(source)
    if (!Array.isArray(games)) throw new GameDataError('游戏数据格式错误')
    return games
  } catch (error) {
    if (error instanceof GameDataError) throw error
    throw new GameDataError()
  }
}

async function getGameDetail(gameId) {
  const normalizedId = String(gameId).trim().toLowerCase()
  const games = await readGames()
  const game = games.find((item) => String(item.id).toLowerCase() === normalizedId)

  if (!game) throw new GameNotFoundError(gameId)
  return game
}

module.exports = {
  GameDataError,
  GameNotFoundError,
  getGameDetail
}
