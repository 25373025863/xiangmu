import { addFavorite } from '../api/favoriteApi.js'
import { getRecommendations } from '../api/recommendApi.js'
import { GameCard, hydrateGameCardCovers } from '../components/GameCard.js'
import { readProviderConfig } from '../utils/providerConfig.js'

export function RecommendPage() {
  return {
    html: `
      <section class="page">
        <div class="page-heading"><div><p class="eyebrow">推荐结果</p><h1>本轮推荐</h1></div><span class="status status--done">已联调</span></div>
        <div id="recommend-grid" class="game-grid"><div class="loading-state">正在生成推荐...</div></div>
      </section>`,
    async mount() {
      const grid = document.querySelector('#recommend-grid')
      const fallback = { genres: [], platforms: [], player_mode: '单人' }
      const preferences = JSON.parse(sessionStorage.getItem('lastPreference') || JSON.stringify(fallback))
      const providerConfig = readProviderConfig()
      try {
        const result = await getRecommendations(preferences, providerConfig)
        grid.innerHTML = result.data.length
          ? result.data.map(game => GameCard(game, { favoriteAction: true })).join('')
          : '<div class="empty-state">当前没有推荐结果，请先完善偏好。</div>'
        hydrateGameCardCovers(grid)
        grid.addEventListener('click', async event => {
          const button = event.target.closest('[data-favorite-game]')
          if (!button) return
          button.disabled = true
          try {
            const result = await addFavorite(decodeURIComponent(button.dataset.favoriteGame))
            button.textContent = result.created ? '已收藏' : '已收藏'
            button.title = '已收藏'
          } catch (error) {
            button.disabled = false
            window.alert(error.message)
          }
        })
      } catch (error) {
        grid.innerHTML = `<div class="error-state">${error.message}</div>`
      }
    }
  }
}
