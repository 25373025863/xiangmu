import { getCatalogueGames } from '../api/catalogueApi.js'
import { checkConfig } from '../api/keyApi.js'
import { escapeHtml } from '../utils/format.js'

const PAGE_SIZE = 12

const heroGames = [
  ['哈迪斯', 'https://cdn.akamai.steamstatic.com/steam/apps/1145360/library_hero.jpg'],
  ['星露谷物语', 'https://cdn.akamai.steamstatic.com/steam/apps/413150/library_hero.jpg'],
  ['双人成行', 'https://cdn.akamai.steamstatic.com/steam/apps/1426210/library_hero.jpg'],
  ['文明 VI', 'https://cdn.akamai.steamstatic.com/steam/apps/289070/library_hero.jpg']
]

function safeWebUrl(value) {
  if (!value) return ''
  try {
    const url = new URL(String(value), window.location.origin)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : ''
  } catch {
    return ''
  }
}

function steamStoreUrl(value, title) {
  const candidate = safeWebUrl(value)
  if (candidate) {
    const hostname = new URL(candidate).hostname.toLowerCase()
    if (hostname === 'store.steampowered.com' || hostname.endsWith('.store.steampowered.com')) {
      return candidate
    }
  }
  return `https://store.steampowered.com/search/?term=${encodeURIComponent(title)}`
}

function asList(value) {
  if (Array.isArray(value)) return value.filter(Boolean).map(String)
  return value ? [String(value)] : []
}

function isSteamSource(source) {
  return String(source || '').toLowerCase().includes('steam')
}

function catalogueCard(game, catalogueSource) {
  const title = String(game.title || '未命名游戏')
  const coverUrl = safeWebUrl(game.cover_url)
  const storeUrl = steamStoreUrl(game.store_url, title)
  const platforms = asList(game.platforms).slice(0, 3)
  const hasScore = game.review_score !== null && game.review_score !== undefined && Number.isFinite(Number(game.review_score))
  const score = hasScore ? Math.max(0, Math.min(100, Math.round(Number(game.review_score)))) : null
  const source = game.source || catalogueSource
  const sourceLabel = isSteamSource(source) ? 'STEAM' : 'LOCAL'

  return `
    <article class="catalogue-card" role="listitem">
      <div class="catalogue-card__cover">
        <span class="catalogue-cover-placeholder" aria-hidden="true"><strong>${escapeHtml(title)}</strong><small>GAME // SELECT</small></span>
        ${coverUrl ? `<img data-catalogue-cover src="${escapeHtml(coverUrl)}" alt="${escapeHtml(title)} 游戏封面" width="460" height="215" loading="lazy" decoding="async" />` : ''}
        <span class="catalogue-card__source">${sourceLabel}</span>
      </div>
      <div class="catalogue-card__body">
        <div class="catalogue-card__heading">
          <h3>${escapeHtml(title)}</h3>
          ${score === null ? '' : `<strong class="catalogue-score" aria-label="好评率 ${score}%">${score}%</strong>`}
        </div>
        <p class="catalogue-card__review">${escapeHtml(game.review_label || '暂无评测摘要')}</p>
        <div class="catalogue-card__platforms" aria-label="支持平台">
          ${(platforms.length ? platforms : ['平台未注明']).map(platform => `<span>${escapeHtml(platform)}</span>`).join('')}
        </div>
        <dl class="catalogue-card__facts">
          <div><dt>发行</dt><dd>${escapeHtml(game.release_date || '未注明')}</dd></div>
          <div><dt>价格</dt><dd>${escapeHtml(game.price || '未注明')}</dd></div>
        </dl>
        <a class="button button--secondary catalogue-card__action" href="${escapeHtml(storeUrl)}" target="_blank" rel="noopener noreferrer" aria-label="在 Steam 查看 ${escapeHtml(title)}">在 Steam 查看</a>
      </div>
    </article>`
}

function catalogueSkeletons() {
  return Array.from({ length: PAGE_SIZE }, () => `
    <article class="catalogue-card catalogue-card--skeleton" aria-hidden="true">
      <div class="catalogue-card__cover"></div>
      <div class="catalogue-card__body"><span></span><span></span><span></span></div>
    </article>`).join('')
}

export function HomePage() {
  return {
    html: `
      <section class="home-hero" aria-labelledby="home-title">
        <div class="home-hero__media" aria-hidden="true">
          ${heroGames.map(([, image]) => `<img src="${image}" alt="" width="768" height="432" fetchpriority="high" />`).join('')}
        </div>
        <div class="home-hero__content">
          <p class="home-kicker"><i data-lucide="bot"></i> AI GAME RECOMMENDATION</p>
          <h1 id="home-title">GAME // SELECT</h1>
          <p class="home-hero__lead">把你的时间、平台和偏好，转化成下一款值得投入的游戏。</p>
          <div class="home-hero__actions">
            <a class="button button--signal" data-link href="/preferences">开始推荐 <i data-lucide="arrow-right"></i></a>
            <a class="button button--ghost" href="#game-catalogue">浏览游戏库</a>
          </div>
          <div class="home-hero__status" aria-live="polite">
            <span class="signal-dot"></span><span id="home-api-status">正在连接推荐服务与 Steam 目录...</span>
          </div>
        </div>
      </section>

      <section class="home-section home-section--flow" aria-labelledby="flow-title">
        <div class="home-section__heading">
          <p class="eyebrow">你的输入，清晰地决定结果</p>
          <h2 id="flow-title">从偏好到候选，只走三步。</h2>
        </div>
        <div class="home-flow">
          <article><span>01</span><i data-lucide="sliders-horizontal"></i><h3>填写偏好</h3><p>选择类型、平台、预算和游玩方式，也可补充 Steam 公开资料。</p></article>
          <article><span>02</span><i data-lucide="sparkles"></i><h3>生成推荐</h3><p>候选游戏与个人偏好共同进入推荐逻辑，保留匹配理由和注意事项。</p></article>
          <article><span>03</span><i data-lucide="heart"></i><h3>保存记录</h3><p>收藏有兴趣的游戏，历史页面会保留本轮偏好和推荐结果。</p></article>
        </div>
      </section>

      <section id="game-catalogue" class="home-section home-section--catalog" aria-labelledby="catalog-title" tabindex="-1">
        <div class="home-section__heading home-section__heading--row">
          <div>
            <p class="eyebrow">Steam 在线目录</p>
            <h2 id="catalog-title">在首页直接发现下一款游戏。</h2>
          </div>
          <span id="catalogue-source" class="catalogue-source catalogue-source--loading">CONNECTING</span>
        </div>

        <form id="catalogue-controls" class="catalogue-controls" role="search">
          <label class="catalogue-field catalogue-field--search">
            <span>搜索游戏</span>
            <span class="catalogue-searchbox">
              <i data-lucide="search"></i>
              <input id="catalogue-keyword" name="keyword" type="search" autocomplete="off" placeholder="输入游戏名称" />
              <button id="catalogue-clear" type="button" aria-label="清除搜索" title="清除搜索" hidden><i data-lucide="x"></i></button>
            </span>
          </label>
          <label class="catalogue-field">
            <span>排序方式</span>
            <select id="catalogue-sort" name="sort">
              <option value="topsellers">畅销优先</option>
              <option value="released">最新发布</option>
              <option value="price">价格从低</option>
              <option value="name">名称排序</option>
            </select>
          </label>
          <button class="button catalogue-controls__submit" type="submit"><i data-lucide="search"></i>检索目录</button>
        </form>

        <div class="catalogue-toolbar">
          <p id="catalogue-summary" aria-live="polite">正在获取 Steam 游戏目录...</p>
          <p id="catalogue-progress" role="status" aria-live="polite" aria-atomic="true"></p>
        </div>
        <div id="catalogue-fallback" class="catalogue-fallback" role="status" hidden></div>
        <div id="catalogue-feedback" class="catalogue-feedback" hidden></div>
        <div id="catalogue-grid" class="catalogue-grid" role="list" aria-busy="true">${catalogueSkeletons()}</div>
        <div class="catalogue-load-zone">
          <div id="catalogue-load-trigger" class="catalogue-load-trigger" aria-hidden="true"></div>
          <button id="catalogue-load-more" class="button button--ghost" type="button" hidden>加载更多游戏</button>
        </div>
      </section>

      <section class="home-section home-section--system" aria-labelledby="system-title">
        <div class="system-line"><i data-lucide="shield-check"></i><div><p class="eyebrow">私密信息留在你的会话中</p><h2 id="system-title">API Key 仅通过请求头使用，服务端不会保存或返回真实密钥。</h2></div><a class="button button--ghost" data-link href="/settings">管理 Key</a></div>
      </section>`,
    mount() {
      const section = document.querySelector('#game-catalogue')
      if (!section) return undefined

      const form = section.querySelector('#catalogue-controls')
      const keywordInput = section.querySelector('#catalogue-keyword')
      const sortSelect = section.querySelector('#catalogue-sort')
      const clearButton = section.querySelector('#catalogue-clear')
      const grid = section.querySelector('#catalogue-grid')
      const feedback = section.querySelector('#catalogue-feedback')
      const fallback = section.querySelector('#catalogue-fallback')
      const summary = section.querySelector('#catalogue-summary')
      const progress = section.querySelector('#catalogue-progress')
      const sourceBadge = section.querySelector('#catalogue-source')
      const loadButton = section.querySelector('#catalogue-load-more')
      const loadTrigger = section.querySelector('#catalogue-load-trigger')
      const heroStatus = document.querySelector('#home-api-status')

      const numberFormat = new Intl.NumberFormat('zh-CN')
      const state = { keyword: '', sort: 'topsellers', page: 0, failedPage: null, total: 0, hasMore: false, source: '', items: [] }
      let activeController = null
      let debounceTimer = null
      let disposed = false
      let loading = false
      let requestVersion = 0
      let catalogueResolved = false
      let autoLoadEnabled = false

      const observer = 'IntersectionObserver' in window
        ? new IntersectionObserver(entries => {
            if (autoLoadEnabled && entries.some(entry => entry.isIntersecting)) loadNextPage()
          }, { rootMargin: '320px 0px' })
        : null

      function updateClearButton() {
        clearButton.hidden = !keywordInput.value
      }

      function updateLoadControls() {
        const loaded = state.items.length
        progress.textContent = loaded ? `已显示 ${numberFormat.format(loaded)} / ${numberFormat.format(state.total)}` : ''
        loadButton.hidden = !state.hasMore || loaded === 0
        loadButton.disabled = loading
        loadButton.textContent = loading ? '正在加载...' : '加载更多游戏'
      }

      function hydrateCoverImages(container) {
        container.querySelectorAll('img[data-catalogue-cover]:not([data-cover-bound])').forEach(image => {
          image.dataset.coverBound = 'true'
          const cover = image.closest('.catalogue-card__cover')
          const reveal = () => cover?.classList.add('is-cover-ready')
          const fail = () => {
            cover?.classList.add('is-cover-unavailable')
            image.remove()
          }
          image.addEventListener('load', reveal, { once: true })
          image.addEventListener('error', fail, { once: true })
          if (image.complete) {
            if (image.naturalWidth > 0) reveal()
            else fail()
          }
        })
      }

      function showFeedback(kind, message, action = '') {
        feedback.hidden = false
        feedback.innerHTML = `
          <div class="${kind === 'error' ? 'error-state' : 'empty-state'}">
            <h3>${kind === 'error' ? '目录加载失败' : '没有找到匹配的游戏'}</h3>
            <p>${escapeHtml(message)}</p>
            ${action === 'clear' ? '<button class="button button--ghost" type="button" data-catalogue-clear>清除搜索</button>' : ''}
            ${action === 'retry' ? '<button class="button button--ghost" type="button" data-catalogue-retry>重新加载</button>' : ''}
          </div>`
      }

      function clearFeedback() {
        feedback.hidden = true
        feedback.replaceChildren()
      }

      function renderResponse(data, incomingItems, reset) {
        if (reset) grid.replaceChildren()
        if (incomingItems.length) {
          grid.insertAdjacentHTML('beforeend', incomingItems.map(game => catalogueCard(game, data.source)).join(''))
          hydrateCoverImages(grid)
        }
        grid.hidden = state.items.length === 0
        grid.setAttribute('aria-busy', 'false')

        if (state.items.length === 0) {
          const message = state.keyword ? `没有与“${state.keyword}”匹配的 Steam 游戏，请换一个关键词。` : '当前目录没有可展示的游戏，请稍后重试。'
          showFeedback('empty', message, state.keyword ? 'clear' : 'retry')
        } else {
          clearFeedback()
        }

        const steamSource = isSteamSource(data.source)
        sourceBadge.className = `catalogue-source ${steamSource ? 'catalogue-source--online' : 'catalogue-source--fallback'}`
        sourceBadge.textContent = steamSource ? 'STEAM ONLINE' : 'LOCAL FALLBACK'
        summary.textContent = state.keyword
          ? `找到 ${numberFormat.format(state.total)} 款相关游戏`
          : `${steamSource ? 'Steam 在线目录' : '本地备用目录'} · ${numberFormat.format(state.total)} 款游戏`

        fallback.hidden = !data.fallback_message
        fallback.textContent = data.fallback_message || ''
        if (heroStatus && !state.keyword) {
          heroStatus.textContent = steamSource
            ? `推荐服务在线 · Steam 目录 ${numberFormat.format(state.total)} 款`
            : `推荐服务在线 · 本地目录 ${numberFormat.format(state.total)} 款`
        }
        updateLoadControls()
      }

      async function loadPage(page, { reset = false } = {}) {
        if (loading && !reset) return
        activeController?.abort()
        const controller = new AbortController()
        activeController = controller
        const version = ++requestVersion
        loading = true
        grid.setAttribute('aria-busy', 'true')

        if (reset) {
          state.page = 0
          state.total = 0
          state.hasMore = false
          state.items = []
          grid.hidden = false
          grid.innerHTML = catalogueSkeletons()
          clearFeedback()
          fallback.hidden = true
          summary.textContent = '正在获取 Steam 游戏目录...'
          progress.textContent = ''
          sourceBadge.className = 'catalogue-source catalogue-source--loading'
          sourceBadge.textContent = 'CONNECTING'
        }
        updateLoadControls()

        try {
          const result = await getCatalogueGames({
            keyword: state.keyword,
            sort: state.sort,
            page,
            size: PAGE_SIZE
          }, { signal: controller.signal })
          if (disposed || version !== requestVersion) return

          const data = result?.data
          if (!data || !Array.isArray(data.items)) throw new Error('目录服务返回了无法识别的数据。')
          const existingIds = new Set(reset ? [] : state.items.map(item => String(item.id)))
          const incomingItems = data.items.filter(item => {
            const id = String(item.id || '')
            if (!id || existingIds.has(id)) return false
            existingIds.add(id)
            return true
          })
          state.items = reset ? incomingItems : [...state.items, ...incomingItems]
          state.total = Number.isFinite(Number(data.total)) ? Number(data.total) : state.items.length
          state.page = Number.isFinite(Number(data.page)) ? Number(data.page) : page
          state.failedPage = null
          state.hasMore = Boolean(data.has_more)
          state.source = data.source || ''
          catalogueResolved = true
          renderResponse(data, incomingItems, reset)
        } catch (error) {
          if (error.name === 'AbortError' || disposed || version !== requestVersion) return
          if (reset) {
            grid.replaceChildren()
            grid.hidden = true
          }
          grid.setAttribute('aria-busy', 'false')
          state.failedPage = page
          state.hasMore = !reset && state.items.length > 0
          summary.textContent = 'Steam 目录暂时无法连接'
          sourceBadge.className = 'catalogue-source catalogue-source--error'
          sourceBadge.textContent = 'CONNECTION ERROR'
          showFeedback('error', error.message || '请检查网络后重试。', 'retry')
          if (heroStatus) heroStatus.textContent = '推荐服务在线 · Steam 目录连接失败'
          updateLoadControls()
        } finally {
          if (!disposed && version === requestVersion) {
            loading = false
            activeController = null
            updateLoadControls()
          }
        }
      }

      function applyFilters(force = false) {
        const nextKeyword = keywordInput.value.trim()
        const nextSort = sortSelect.value
        if (!force && nextKeyword === state.keyword && nextSort === state.sort) return
        state.keyword = nextKeyword
        state.sort = nextSort
        loadPage(1, { reset: true })
      }

      function loadNextPage() {
        if (!loading && state.hasMore) loadPage(state.page + 1)
      }

      function clearSearch() {
        keywordInput.value = ''
        updateClearButton()
        applyFilters(true)
        keywordInput.focus()
      }

      function enableAutoLoad() {
        if (autoLoadEnabled) return
        autoLoadEnabled = true
        observer?.observe(loadTrigger)
      }

      form.addEventListener('submit', event => {
        event.preventDefault()
        clearTimeout(debounceTimer)
        applyFilters(true)
      })
      keywordInput.addEventListener('input', () => {
        updateClearButton()
        clearTimeout(debounceTimer)
        debounceTimer = window.setTimeout(() => applyFilters(), 320)
      })
      sortSelect.addEventListener('change', () => {
        clearTimeout(debounceTimer)
        applyFilters(true)
      })
      clearButton.addEventListener('click', clearSearch)
      loadButton.addEventListener('click', loadNextPage)
      section.addEventListener('click', event => {
        if (event.target.closest('[data-catalogue-clear]')) clearSearch()
        if (event.target.closest('[data-catalogue-retry]')) {
          const retryPage = state.failedPage || (state.items.length ? state.page + 1 : 1)
          loadPage(retryPage, { reset: state.items.length === 0 })
        }
      })
      window.addEventListener('scroll', enableAutoLoad, { once: true, passive: true })

      checkConfig()
        .then(() => {
          if (!disposed && !catalogueResolved && heroStatus) heroStatus.textContent = '推荐服务在线 · 正在同步 Steam 目录'
        })
        .catch(() => {
          if (!disposed && !catalogueResolved && heroStatus) heroStatus.textContent = '推荐服务暂不可用，游戏目录仍可浏览'
        })
      loadPage(1, { reset: true })

      return () => {
        disposed = true
        requestVersion += 1
        activeController?.abort()
        clearTimeout(debounceTimer)
        observer?.disconnect()
        window.removeEventListener('scroll', enableAutoLoad)
      }
    }
  }
}
