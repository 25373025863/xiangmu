import { GameCard } from '../components/GameCard.js'
import { getFavorites, removeFavorite } from '../api/favoriteApi.js'

export function FavoritePage() {
  return {
    html: `
      <section class="page">
        <div class="page-heading"><div><p class="eyebrow">我的收藏</p><h1>收藏游戏</h1></div><span class="status status--done">已持久化</span></div>
        <div id="favorite-grid" class="game-grid"><div class="loading-state">正在加载收藏...</div></div>
      </section>`,
    mount() {
      const grid = document.querySelector('#favorite-grid')
      const load = async () => {
        grid.innerHTML = '<div class="loading-state">正在加载收藏...</div>'
        try {
          const result = await getFavorites()
          const items = result.data.list
          grid.innerHTML = items.length
            ? items.map(game => GameCard(game, { removeFavorite: true })).join('')
            : '<div class="empty-state">暂时没有收藏游戏。</div>'
        } catch (error) {
          grid.innerHTML = `<div class="error-state">${error.message}</div>`
        }
      }
      grid.addEventListener('click', async event => {
        const button = event.target.closest('[data-remove-favorite]')
        if (!button) return
        button.disabled = true
        try {
          await removeFavorite(decodeURIComponent(button.dataset.removeFavorite))
          await load()
        } catch (error) {
          button.disabled = false
          window.alert(error.message)
        }
      })
      load()
    }
  }
}
