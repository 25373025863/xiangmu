import { getGame } from '../api/gameApi.js'
import { escapeHtml, joinText } from '../utils/format.js'
import { steamStoreUrl } from '../utils/gameLinks.js'

export function GameDetailPage({ gameId }) {
  const remoteMatch = String(gameId).match(/^steam-(\d+)$/i)
  if (remoteMatch) {
    const storeUrl = steamStoreUrl('', gameId, Number(remoteMatch[1]))
    return {
      html: `
        <section class="page page--narrow">
          <div class="detail-layout">
            <div><p class="eyebrow">STEAM CATALOGUE</p><h1>在线游戏详情</h1><p class="detail-copy">该游戏来自 Steam 在线目录，请前往商店查看完整介绍、价格和系统需求。</p></div>
            <div class="actions"><a class="button" href="${escapeHtml(storeUrl)}" target="_blank" rel="noopener noreferrer">在 Steam 查看</a><a class="button button--secondary" data-link href="/#game-catalogue">返回游戏目录</a></div>
          </div>
        </section>`
    }
  }
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
