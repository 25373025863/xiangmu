const express = require('express')

const { getGameById } = require('../controllers/gameController')

const router = express.Router()

router.get('/:id', getGameById)

module.exports = router
