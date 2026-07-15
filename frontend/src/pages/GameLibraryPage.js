import { getGames } from '../api/gameApi.js'
import { GameCard } from '../components/GameCard.js'

export function GameLibraryPage() {
  return {
    html: `
      <section class="page">
        <div class="page-heading"><div><p class="eyebrow">游戏数据</p><h1>游戏库</h1></div><span class="status status--done">统一 ID</span></div>
        <form id="game-filter" class="filter-bar"><input name="keyword" placeholder="搜索名称、标签或描述" /><input name="genre" placeholder="类型" /><input name="platform" placeholder="平台" /><button class="button" type="submit">筛选</button></form>
        <div id="game-grid" class="game-grid"><p class="muted">正在加载游戏数据...</p></div>
      </section>`,
    mount() {
      const form = document.querySelector('#game-filter')
      const grid = document.querySelector('#game-grid')
      const load = async () => {
        grid.innerHTML = '<p class="muted">正在加载游戏数据...</p>'
        try {
          const result = await getGames(Object.fromEntries(new FormData(form)))
          grid.innerHTML = result.data.items.length
            ? result.data.items.map(game => GameCard(game)).join('')
            : '<div class="empty-state">没有符合条件的游戏。</div>'
        } catch (error) {
          grid.innerHTML = `<div class="error-state">${error.message}</div>`
        }
      }
      form.addEventListener('submit', event => { event.preventDefault(); load() })
      load()
    }
  }
}
