import { FavoritePage } from './pages/FavoritePage.js'
import { GameDetailPage } from './pages/GameDetailPage.js'
import { HelpPage } from './pages/HelpPage.js'
import { HistoryPage } from './pages/HistoryPage.js'
import { HomePage } from './pages/HomePage.js'
import { PreferencePage } from './pages/PreferencePage.js'
import { RecommendPage } from './pages/RecommendPage.js'
import { SettingsPage } from './pages/SettingsPage.js'
import {
  ArrowRight,
  Bot,
  Database,
  Eye,
  EyeOff,
  Heart,
  History,
  LoaderCircle,
  Save,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Search,
  Trash2,
  X,
  createIcons
} from 'lucide'

const icons = { ArrowRight, Bot, Database, Eye, EyeOff, Heart, History, LoaderCircle, Save, ShieldCheck, SlidersHorizontal, Sparkles, Search, Trash2, X }

const routes = [
  { pattern: /^\/$/, create: HomePage },
  { pattern: /^\/preferences$/, create: PreferencePage },
  { pattern: /^\/games\/([^/]+)$/, create: match => GameDetailPage({ gameId: decodeURIComponent(match[1]) }) },
  { pattern: /^\/recommend$/, create: RecommendPage },
  { pattern: /^\/favorites$/, create: FavoritePage },
  { pattern: /^\/histories$/, create: HistoryPage },
  { pattern: /^\/settings$/, create: SettingsPage },
  { pattern: /^\/help$/, create: HelpPage }
]

function resolvePage(pathname) {
  for (const route of routes) {
    const match = pathname.match(route.pattern)
    if (match) return route.create(match)
  }
  return { html: '<section class="page"><div class="error-state">页面不存在。</div></section>' }
}

export function createApp(root) {
  root.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <a class="brand" data-link href="/">GAME / SELECT</a>
        <nav aria-label="主导航">
          <a data-link href="/preferences">偏好</a><a data-link href="/recommend">推荐</a><a data-link href="/favorites">收藏</a><a data-link href="/histories">历史</a><a data-link href="/settings">设置</a><a data-link href="/help">帮助</a>
        </nav>
      </header>
      <main id="route-view"></main>
    </div>`

  let disposePage = null

  const render = () => {
    disposePage?.()
    disposePage = null

    if (window.location.pathname === '/games') {
      window.history.replaceState({}, '', '/#game-catalogue')
    }
    const page = resolvePage(window.location.pathname)
    const view = root.querySelector('#route-view')
    view.innerHTML = page.html
    root.querySelectorAll('nav a').forEach(link => {
      link.classList.toggle('active', link.getAttribute('href') === window.location.pathname)
    })
    const cleanup = page.mount?.()
    if (typeof cleanup === 'function') disposePage = cleanup
    createIcons({ icons, attrs: { 'aria-hidden': 'true', focusable: 'false' } })
    if (window.location.hash === '#game-catalogue') {
      window.requestAnimationFrame(() => {
        const catalogue = root.querySelector('#game-catalogue')
        catalogue?.scrollIntoView({ block: 'start' })
        catalogue?.focus({ preventScroll: true })
      })
    } else {
      window.scrollTo(0, 0)
    }
  }

  root.addEventListener('click', event => {
    const link = event.target.closest('a[data-link]')
    if (!link || link.origin !== window.location.origin) return
    event.preventDefault()
    window.history.pushState({}, '', `${link.pathname}${link.search}${link.hash}`)
    render()
  })
  window.addEventListener('popstate', render)
  render()
}
