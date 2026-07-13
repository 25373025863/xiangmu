const assert = require('node:assert/strict')
const { once } = require('node:events')
const test = require('node:test')

const app = require('../src/app')
const { GameNotFoundError, getGameDetail } = require('../src/services/gameService')

let server
let apiBaseUrl

test.before(async () => {
  server = app.listen(0, '127.0.0.1')
  await once(server, 'listening')
  apiBaseUrl = `http://127.0.0.1:${server.address().port}/api`
})

test.after(async () => {
  server.close()
  await once(server, 'close')
})

test('returns a complete game detail by ID', async () => {
  const game = await getGameDetail('g003')

  assert.equal(game.id, 'g003')
  assert.equal(game.title, '哈迪斯')
  assert.ok(game.cover)
  assert.ok(game.suitableFor.length)
})

test('throws GameNotFoundError for an unknown game ID', async () => {
  await assert.rejects(getGameDetail('missing-game'), GameNotFoundError)
})

test('serves complete game detail through the API route', async () => {
  const response = await fetch(`${apiBaseUrl}/games/g003`)

  assert.equal(response.status, 200)
  assert.deepEqual(await response.json(), {
    code: 0,
    message: 'success',
    data: await getGameDetail('g003')
  })
})

test('returns a structured 404 response for an unknown game ID', async () => {
  const response = await fetch(`${apiBaseUrl}/games/missing-game`)

  assert.equal(response.status, 404)
  assert.deepEqual(await response.json(), {
    code: 'GAME_NOT_FOUND',
    message: '游戏不存在',
    data: null
  })
})
