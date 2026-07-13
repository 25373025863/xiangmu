<template>
  <main class="detail-page">
    <button class="back-button" type="button" @click="goBack">返回上一页</button>

    <section v-if="status === 'loading'" class="state-panel" aria-live="polite">
      <p>正在加载游戏详情...</p>
    </section>

    <section v-else-if="status === 'error'" class="state-panel" aria-live="polite">
      <h1>{{ errorStatus === 404 ? '未找到这款游戏' : '游戏详情暂时无法加载' }}</h1>
      <p>{{ errorMessage }}</p>
      <div class="state-actions">
        <button v-if="errorStatus !== 404" type="button" @click="loadDetail">重试</button>
        <button class="secondary-button" type="button" @click="goBack">返回上一页</button>
      </div>
    </section>

    <template v-else-if="game">
      <section class="game-hero" aria-labelledby="game-title">
        <img
          v-if="game.cover && !imageFailed"
          class="game-cover"
          :src="game.cover"
          :alt="`${game.title} 游戏封面`"
          @error="imageFailed = true"
        >
        <div v-else class="cover-fallback" :aria-label="`${game.title} 封面缺失`">{{ game.title }}</div>

        <div class="hero-content">
          <p class="eyebrow">游戏详情</p>
          <h1 id="game-title">{{ game.title }}</h1>
          <div class="quick-facts">
            <span v-if="game.score !== null">评分 {{ game.score }}/10</span>
            <span v-if="game.price">{{ game.price }}</span>
            <span v-if="game.release_date">{{ game.release_date }}</span>
          </div>
          <ul v-if="game.tags.length" class="tag-list" aria-label="游戏标签">
            <li v-for="tag in game.tags" :key="tag">{{ tag }}</li>
          </ul>
        </div>
      </section>

      <div class="detail-layout">
        <section class="detail-section description-section" aria-labelledby="description-title">
          <h2 id="description-title">游戏简介</h2>
          <p>{{ game.description }}</p>
        </section>

        <aside class="detail-section meta-section" aria-label="游戏基本资料">
          <dl>
            <div><dt>平台</dt><dd>{{ game.platforms.join('、') || '暂无信息' }}</dd></div>
            <div><dt>类型</dt><dd>{{ game.genres.join('、') || '暂无信息' }}</dd></div>
            <div v-if="game.developer"><dt>开发商</dt><dd>{{ game.developer }}</dd></div>
          </dl>
        </aside>

        <section class="detail-section" aria-labelledby="suitable-title">
          <h2 id="suitable-title">适合人群</h2>
          <ul class="check-list">
            <li v-for="person in game.suitable_for" :key="person">{{ person }}</li>
            <li v-if="!game.suitable_for.length">暂无信息</li>
          </ul>
        </section>

        <section v-if="recommendationReason" class="detail-section recommendation-section" aria-labelledby="reason-title">
          <h2 id="reason-title">推荐理由</h2>
          <p>{{ recommendationReason }}</p>
        </section>
      </div>

      <a
        v-if="game.purchase_url"
        class="purchase-link"
        :href="game.purchase_url"
        target="_blank"
        rel="noreferrer"
      >
        前往购买或了解更多
      </a>
    </template>
  </main>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { GameApiError, getGameDetail } from '../api/gameApi'

const route = useRoute()
const router = useRouter()
const game = ref(null)
const status = ref('loading')
const errorStatus = ref(null)
const errorMessage = ref('')
const imageFailed = ref(false)

const recommendationReason = computed(() => {
  const routeReason = route.query.reason
  if (typeof routeReason === 'string' && routeReason) return routeReason
  return sessionStorage.getItem(`recommendation-reason:${route.params.gameId}`)
})

async function loadDetail() {
  const controller = new AbortController()
  status.value = 'loading'
  errorStatus.value = null
  imageFailed.value = false

  try {
    game.value = await getGameDetail(route.params.gameId, controller.signal)
    status.value = 'ready'
  } catch (error) {
    if (error.name === 'AbortError') return
    errorStatus.value = error instanceof GameApiError ? error.status : null
    errorMessage.value = error.message || '请检查后端服务是否已启动。'
    status.value = 'error'
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

watch(() => route.params.gameId, loadDetail, { immediate: true })
</script>

<style scoped>
.detail-page { max-width: 1120px; margin: 0 auto; padding: 28px 20px 52px; color: #1f2937; }
.back-button, .secondary-button { min-height: 38px; padding: 0 14px; border: 1px solid #94a3b8; border-radius: 5px; background: #fff; color: #334155; }
.back-button:hover, .secondary-button:hover { border-color: #2563eb; color: #1d4ed8; }
.state-panel { display: grid; min-height: 50vh; place-content: center; text-align: center; }
.state-panel p { color: #64748b; line-height: 1.6; }
.state-actions { display: flex; justify-content: center; gap: 10px; }
.game-hero { display: grid; grid-template-columns: minmax(210px, 320px) minmax(0, 1fr); gap: 40px; margin: 30px 0 38px; align-items: end; }
.game-cover, .cover-fallback { display: block; width: 100%; aspect-ratio: 3 / 4; border-radius: 6px; background: #dbeafe; object-fit: cover; }
.cover-fallback { display: grid; place-items: center; padding: 20px; color: #1e3a8a; text-align: center; font-size: 24px; font-weight: 700; }
.eyebrow { margin: 0 0 8px; color: #0f766e; font-size: 13px; font-weight: 700; }
h1 { margin: 0 0 16px; font-size: 40px; line-height: 1.12; letter-spacing: 0; }
h2 { margin: 0 0 14px; font-size: 20px; letter-spacing: 0; }
.quick-facts { display: flex; flex-wrap: wrap; gap: 8px 20px; color: #475569; }
.tag-list { display: flex; flex-wrap: wrap; gap: 8px; margin: 20px 0 0; padding: 0; list-style: none; }
.tag-list li { padding: 5px 9px; border: 1px solid #0f766e; border-radius: 4px; color: #0f766e; font-size: 13px; }
.detail-layout { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 20px; }
.detail-section { padding: 24px 0; border-top: 1px solid #cbd5e1; }
.detail-section p, dd, .check-list { color: #475569; line-height: 1.7; }
.description-section, .recommendation-section { grid-column: 1; }
.meta-section { grid-column: 2; grid-row: 1 / span 2; }
dl { margin: 0; }
dl div { padding-bottom: 14px; }
dt { margin-bottom: 4px; color: #64748b; font-size: 13px; }
dd { margin: 0; }
.check-list { margin: 0; padding-left: 20px; }
.check-list li + li { margin-top: 8px; }
.purchase-link { display: inline-flex; align-items: center; min-height: 42px; margin-top: 22px; padding: 0 16px; border-radius: 5px; background: #0f766e; color: #fff; font-weight: 700; text-decoration: none; }
.purchase-link:hover { background: #115e59; }
@media (max-width: 720px) { .game-hero { grid-template-columns: 132px minmax(0, 1fr); gap: 20px; } h1 { font-size: 30px; } .detail-layout { display: block; } .meta-section { border-bottom: 1px solid #cbd5e1; } }
@media (max-width: 440px) { .game-hero { grid-template-columns: 1fr; } .game-cover, .cover-fallback { max-width: 220px; } }
</style>
