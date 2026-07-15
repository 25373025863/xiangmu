import { getGame } from '../api/gameApi.js'
import { escapeHtml, joinText } from '../utils/format.js'

export function GameDetailPage({ gameId }) {
  return {
    html: '<section class="page page--narrow"><div id="game-detail" class="loading-state">正在加载详情...</div></section>',
    async mount() {
      const container = document.querySelector('#game-detail')
      try {
        const result = await getGame(gameId)
        const game = result.data
        container.className = 'detail-layout'
        container.innerHTML = `
          <div><p class="eyebrow">${escapeHtml(joinText(game.genres))}</p><h1>${escapeHtml(game.title)}</h1><p class="detail-copy">${escapeHtml(game.description)}</p></div>
          <dl><dt>平台</dt><dd>${escapeHtml(joinText(game.platforms))}</dd><dt>价格</dt><dd>${escapeHtml(game.price || '未注明')}</dd><dt>评分</dt><dd>${escapeHtml(game.score || '未注明')}</dd><dt>标签</dt><dd>${escapeHtml(joinText(game.tags))}</dd></dl>
          <a class="button button--secondary" data-link href="/games">返回游戏库</a>`
      } catch (error) {
        container.className = 'error-state'
        container.textContent = error.message
      }
    }
  }
}
