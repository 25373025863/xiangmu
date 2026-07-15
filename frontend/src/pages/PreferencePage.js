import { readSteamProfile, submitPreferences } from '../api/recommendApi.js'
import { escapeHtml } from '../utils/format.js'

export function PreferencePage() {
  return {
    html: `
      <section class="page page--narrow">
        <div class="page-heading">
          <div><p class="eyebrow">偏好输入</p><h1>告诉系统你想玩什么</h1></div>
          <span class="status status--done">已接入后端</span>
        </div>
        <form id="preference-form" class="form-layout">
          <label>游戏类型<input name="genres" placeholder="动作, 策略, 模拟经营" required /></label>
          <label>游戏平台<input name="platforms" placeholder="PC, Switch" required /></label>
          <label>预算<select name="budget"><option>100元内</option><option>100-300元</option><option>300元以上</option><option>免费</option></select></label>
          <label>游玩方式<select name="player_mode"><option>单人</option><option>本地多人</option><option>在线多人</option><option>MMO</option></select></label>
          <label>画风偏好<input name="art_style" placeholder="像素、写实、手绘" /></label>
          <label>时长偏好<select name="play_time"><option>适中(10-30h)</option><option>短平快(&lt;10h)</option><option>杀时间(30h+)</option><option>无限游玩</option></select></label>
          <label class="field-wide">其他要求<textarea name="extra_requirements" rows="3" placeholder="例如需要中文、避免高难度"></textarea></label>
          <label class="checkbox field-wide"><input type="checkbox" name="chinese_support" checked />需要中文支持</label>
          <div class="actions field-wide"><button class="button" type="submit">保存并生成推荐</button><span id="preference-status" class="form-status"></span></div>
        </form>
        <div class="section-divider"></div>
        <section>
          <h2>导入 Steam 公开资料</h2>
          <div class="inline-form"><input id="steam-id" placeholder="SteamID、SteamID64 或资料链接" aria-describedby="steam-help" /><button id="steam-submit" class="button button--secondary">读取资料</button></div>
          <p id="steam-help" class="input-help">只读取公开资料和公开游戏库；资料私密时仍可继续手动填写偏好。</p>
          <div id="steam-status" class="form-status"></div>
          <section id="steam-summary" class="steam-summary" hidden aria-live="polite"></section>
        </section>
      </section>`,
    mount() {
      const form = document.querySelector('#preference-form')
      const status = document.querySelector('#preference-status')
      let steamSummary = null
      form.addEventListener('submit', async event => {
        event.preventDefault()
        const data = new FormData(form)
        const split = value => String(value).split(/[,，]/).map(item => item.trim()).filter(Boolean)
        const preferences = {
          genres: split(data.get('genres')),
          platforms: split(data.get('platforms')),
          budget: data.get('budget'),
          player_mode: data.get('player_mode'),
          art_style: data.get('art_style') || null,
          play_time: data.get('play_time'),
          extra_requirements: data.get('extra_requirements') || null,
          chinese_support: data.get('chinese_support') === 'on',
          steam_summary: steamSummary?.visibility === 'public' ? steamSummary : null
        }
        status.textContent = '正在校验...'
        try {
          const result = await submitPreferences(preferences)
          sessionStorage.setItem('lastPreference', JSON.stringify(result.data))
          status.textContent = '偏好已保存，正在进入推荐页。'
          window.history.pushState({}, '', '/recommend')
          window.dispatchEvent(new PopStateEvent('popstate'))
        } catch (error) {
          status.textContent = error.message
        }
      })

      document.querySelector('#steam-submit').addEventListener('click', async () => {
        const input = document.querySelector('#steam-id')
        const button = document.querySelector('#steam-submit')
        const steamStatus = document.querySelector('#steam-status')
        const summary = document.querySelector('#steam-summary')
        if (!input.value.trim()) return
        button.disabled = true
        summary.hidden = true
        steamStatus.textContent = '正在读取公开资料...'
        try {
          const profile = await readSteamProfile(input.value.trim())
          steamSummary = profile
          const topGames = (profile.top_games || []).slice(0, 5)
          const hasLibrary = profile.visibility === 'public'
            && ['steam_web_api', 'public_xml'].includes(profile.data_source)
            && Number(profile.game_count) > 0
          if (hasLibrary) {
            const genreField = form.elements.genres
            const platformField = form.elements.platforms
            genreField.value = mergeCsv(genreField.value, profile.inferred_game_types || [])
            platformField.value = mergeCsv(platformField.value, profile.suggested_platforms || [])
            if (profile.suggested_player_mode) form.elements.player_mode.value = profile.suggested_player_mode
          }
          steamStatus.innerHTML = `<strong>${escapeHtml(profile.profile_name || 'Steam 用户')}</strong>：${escapeHtml(profile.message)}`
          summary.hidden = false
          summary.innerHTML = `
            <div class="steam-summary__head"><strong>${hasLibrary ? '已合并公开游戏库' : '已读取公开资料'}</strong><span>${escapeHtml(profile.data_source || 'profile_only')}</span></div>
            <dl><div><dt>游戏库</dt><dd>${escapeHtml(profile.game_count || 0)} 款</dd></div><div><dt>总时长</dt><dd>${escapeHtml(profile.total_playtime_hours || 0)} 小时</dd></div></dl>
            ${topGames.length ? `<div class="steam-summary__games">${topGames.map(game => `<span>${escapeHtml(game.name)}<small>${escapeHtml(game.hours_played)} 小时</small></span>`).join('')}</div>` : '<p class="steam-summary__empty">当前资料未提供可读取的游戏库，可继续使用手动偏好。</p>'}`
        } catch (error) {
          steamStatus.textContent = error.message
          steamSummary = null
        } finally {
          button.disabled = false
        }
      })
    }
  }
}

function mergeCsv(currentValue, additions) {
  const values = String(currentValue || '').split(/[,，]/).map(value => value.trim()).filter(Boolean)
  for (const item of additions) {
    if (item && !values.includes(item)) values.push(item)
  }
  return values.join(', ')
}
