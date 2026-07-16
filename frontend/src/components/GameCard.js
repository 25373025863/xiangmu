import { escapeHtml, joinText } from '../utils/format.js'
import { Heart, createIcons } from 'lucide'
import {
  isRemoteSteamGame,
  safeWebUrl,
  steamAppId,
  steamStoreUrl
} from '../utils/gameLinks.js'

export function GameCard(game, options = {}) {
  const id = game.id ?? game.game_id
  const title = game.title || '未命名游戏'
  const tags = game.tags || game.genres || []
  const reason = game.reason || game.description || ''
  const score = game.match_score ?? game.score
  const coverUrl = safeWebUrl(game.cover_url)
  const remoteSteamGame = isRemoteSteamGame(game)
  const storeUrl = remoteSteamGame
    ? steamStoreUrl(game.store_url, title, steamAppId(game))
    : ''
  return `
    <article class="game-card${coverUrl ? ' game-card--with-cover' : ''}">
      ${coverUrl ? `
        <div class="game-card__cover">
          <span aria-hidden="true">GAME // SELECT</span>
          <img data-game-card-cover src="${escapeHtml(coverUrl)}" alt="${escapeHtml(title)} 游戏封面" width="460" height="215" loading="lazy" decoding="async" />
          ${remoteSteamGame ? '<small>STEAM</small>' : ''}
        </div>` : ''}
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
      ${remoteSteamGame ? `<a class="button button--secondary" href="${escapeHtml(storeUrl)}" target="_blank" rel="noopener noreferrer">在 Steam 查看</a>` : id ? `<a class="button button--secondary" data-link href="/games/${encodeURIComponent(id)}">查看详情</a>` : ''}
      ${options.favoriteAction && id && !remoteSteamGame ? `<button class="icon-button" data-favorite-game="${encodeURIComponent(id)}" title="收藏游戏" aria-label="收藏 ${escapeHtml(title)}"><i data-lucide="heart"></i></button>` : ''}
      ${options.removeFavorite && id ? `<button class="button button--danger" data-remove-favorite="${encodeURIComponent(id)}">取消收藏</button>` : ''}
    </article>`
}

export function hydrateGameCardCovers(container) {
  container.querySelectorAll('img[data-game-card-cover]:not([data-cover-bound])').forEach(image => {
    image.dataset.coverBound = 'true'
    image.addEventListener('error', () => image.remove(), { once: true })
    if (image.complete && image.naturalWidth === 0) image.remove()
  })
  createIcons({
    icons: { Heart },
    attrs: { 'aria-hidden': 'true', focusable: 'false' }
  })
}
