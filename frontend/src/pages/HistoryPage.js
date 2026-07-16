import { getHistories } from '../api/favoriteApi.js'
import { GameCard, hydrateGameCardCovers } from '../components/GameCard.js'
import { escapeHtml, joinText } from '../utils/format.js'

export function HistoryPage() {
  return {
    html: `
      <section class="page">
        <div class="page-heading"><div><p class="eyebrow">推荐历史</p><h1>历史记录</h1></div><span class="status status--done">自动保存</span></div>
        <div id="history-list" class="history-list"><div class="loading-state">正在加载历史...</div></div>
      </section>`,
    async mount() {
      const container = document.querySelector('#history-list')
      try {
        const result = await getHistories()
        const records = result.data.list
        container.innerHTML = records.length
          ? records.map(record => {
              const preference = record.preferences || {}
              const summary = [
                preference.genres?.length ? `类型：${joinText(preference.genres)}` : '',
                preference.platforms?.length ? `平台：${joinText(preference.platforms)}` : ''
              ].filter(Boolean).join('，') || '未记录偏好'
              return `<article class="history-record"><p class="history-time">${escapeHtml(new Date(record.created_at).toLocaleString('zh-CN'))}</p><h2>${escapeHtml(summary)}</h2><div class="game-grid">${(record.recommendations || []).map(game => GameCard(game)).join('')}</div></article>`
            }).join('')
          : '<div class="empty-state">还没有推荐历史，先生成一次推荐吧。</div>'
        hydrateGameCardCovers(container)
      } catch (error) {
        container.innerHTML = `<div class="error-state">${error.message}</div>`
      }
    }
  }
}
