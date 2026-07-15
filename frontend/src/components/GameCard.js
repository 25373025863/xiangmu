import { escapeHtml, joinText } from '../utils/format.js'

export function GameCard(game, options = {}) {
  const id = game.id ?? game.game_id
  const title = game.title || '未命名游戏'
  const tags = game.tags || game.genres || []
  const reason = game.reason || game.description || ''
  const score = game.match_score ?? game.score
  return `
    <article class="game-card">
      <div class="game-card__head">
        <div>
          <h3>${escapeHtml(title)}</h3>
          <p>${escapeHtml(joinText(game.platforms || []))}</p>
        </div>
        ${score ? `<strong class="score">${escapeHtml(score)}</strong>` : ''}
      </div>
      <div class="tag-list">
        ${tags.slice(0, 5).map(tag => `<span>${escapeHtml(tag)}</span>`).join('')}
      </div>
      ${reason ? `<p class="game-card__reason">${escapeHtml(reason)}</p>` : ''}
      ${game.possible_drawbacks ? `<p class="notice">注意：${escapeHtml(game.possible_drawbacks)}</p>` : ''}
      ${id ? `<a class="button button--secondary" data-link href="/games/${encodeURIComponent(id)}">查看详情</a>` : ''}
      ${options.favoriteAction && id ? `<button class="icon-button" data-favorite-game="${encodeURIComponent(id)}" title="收藏游戏" aria-label="收藏 ${escapeHtml(title)}"><i data-lucide="heart"></i></button>` : ''}
      ${options.removeFavorite && id ? `<button class="button button--danger" data-remove-favorite="${encodeURIComponent(id)}">取消收藏</button>` : ''}
    </article>`
}
