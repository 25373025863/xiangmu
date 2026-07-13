const {
  GameDataError,
  GameNotFoundError,
  getGameDetail
} = require('../services/gameService')

async function getGameById(req, res, next) {
  try {
    const game = await getGameDetail(req.params.id)
    res.status(200).json({
      code: 0,
      message: 'success',
      data: game
    })
  } catch (error) {
    if (error instanceof GameNotFoundError) {
      return res.status(404).json({
        code: 'GAME_NOT_FOUND',
        message: '游戏不存在',
        data: null
      })
    }
    if (error instanceof GameDataError) {
      return res.status(500).json({
        code: 'GAME_DATA_UNAVAILABLE',
        message: '游戏数据暂时不可用',
        data: null
      })
    }
    return next(error)
  }
}

module.exports = { getGameById }
