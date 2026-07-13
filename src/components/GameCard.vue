<template>
  <div class="fav-card">
    <!-- 游戏名称绑定class -->
    <h3 class="game-name">{{ game.name }}</h3>
    <p>{{ game.desc }}</p>
    <span v-if="isFavorite">❤️ 已收藏</span>
    <span v-else>🤍 收藏</span>
  </div>
</template>

<style scoped>
.game-name {
  cursor: pointer;
  transition: color 0.2s ease;
  margin: 0 0 6px;
  font-size: 16px;
}
/* 鼠标悬浮变蓝色 */
.game-name:hover {
  color: #3b82f6;
}
</style>

<script setup>
import { ref, defineProps } from 'vue';
import { addFavorite, delFavorite } from '../api/recommendApi';

// 接收游戏数据
const props = defineProps({
  game: Object,
  isFavorite: {
    type: Boolean,
    default: false
  }
});

const isFav = ref(props.isFavorite);

// 收藏/取消收藏
const handleFav = async () => {
  try {
    if (isFav.value) {
      await delFavorite(props.game.id);
      isFav.value = false;
      alert('取消收藏成功');
    } else {
      await addFavorite(props.game.id);
      isFav.value = true;
      alert('收藏成功');
    }
  } catch (err) {
    alert('操作失败，请重试');
  }
};
</script>

<style scoped>
.game-card {
  position: relative;
  border: 1px solid #eee;
  padding: 12px;
  border-radius: 8px;
}
.fav-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  border: none;
  background: #fff;
  cursor: pointer;
}
</style>