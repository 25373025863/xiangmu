const express = require('express')

const gameRoutes = require('./routes/gameRoutes')

const app = express()

app.use(express.json())

app.get('/api/health', (req, res) => {
  res.json({ code: 0, message: 'success', data: { status: 'ok' } })
})

app.use('/api/games', gameRoutes)

app.use((error, req, res, next) => {
  console.error(error)
  res.status(500).json({
    code: 'INTERNAL_SERVER_ERROR',
    message: '服务器暂时不可用',
    data: null
  })
})

module.exports = app
