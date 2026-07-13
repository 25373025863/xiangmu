<template>
  <article class="game-card">
    <h3 class="game-name">{{ gameName }}</h3>
    <p>{{ gameDescription }}</p>
    <span v-if="isFavorite" class="favorite-status">已收藏</span>
    <button class="detail-button" type="button" @click="openDetail">查看详情</button>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  game: { type: Object, required: true },
  isFavorite: {
    type: Boolean,
    default: false
  }
})

const router = useRouter()
const gameName = computed(() => props.game.title || props.game.name || '未命名游戏')
const gameDescription = computed(() => props.game.reason || props.game.description || props.game.desc || '')

function openDetail() {
  const gameId = props.game.game_id || props.game.id
  if (!gameId) return

  const reason = props.game.reason
  if (reason) sessionStorage.setItem(`recommendation-reason:${gameId}`, reason)
  router.push({
    name: 'game-detail',
    params: { gameId: String(gameId) },
    query: reason ? { reason } : undefined
  })
}
</script>

<style scoped>
.game-card {
  border: 1px solid #eee;
  padding: 14px;
  border-radius: 6px;
  background: #fff;
}
.game-name { margin: 0 0 8px; color: #1e293b; font-size: 16px; }
p { min-height: 40px; margin: 0 0 12px; color: #64748b; line-height: 1.5; }
.favorite-status { display: inline-block; margin: 0 10px 0 0; color: #b45309; font-size: 13px; }
.detail-button { padding: 6px 12px; border: 1px solid #2563eb; border-radius: 4px; background: #fff; color: #2563eb; }
.detail-button:hover { background: #2563eb; color: #fff; }
</style>
