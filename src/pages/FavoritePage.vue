<template>
  <div class="page-favorite">
    <h2 class="page-title">我的收藏</h2>

    <div v-if="list.length === 0" class="empty-wrap">
      <p class="empty-text">暂无收藏游戏，快去推荐页面收藏心仪游戏吧</p>
    </div>

    <div v-else class="game-grid">
      <!-- 绑定随机背景色style -->
      <div
          class="fav-item"
          v-for="item in list"
          :key="item.id"
          :style="{ backgroundColor: item.bgColor }"
      >
        <GameCard :game="item" :is-favorite="true" />
        <div class="item-footer">
          <span class="fav-time">收藏时间：{{ formatTime(item.favTime) }}</span>
          <button class="cancel-btn" @click="removeFav(item.id)">取消收藏</button>
        </div>
      </div>
    </div>

    <div class="pagination">
      <button :disabled="page <= 1" @click="page--">上一页</button>
      <span class="page-num">第 {{ page }} 页</span>
      <button :disabled="page * pageSize >= total" @click="page++">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import GameCard from '../components/GameCard.vue';
import { getFavoriteList, delFavorite } from '../api/recommendApi';
import { formatTime } from '../utils/format';

const list = ref([]);
const page = ref(1);
const pageSize = 10;
const total = ref(0);

// 红橙黄绿青蓝紫 低饱和浅背景色
const colorPool = [
  '#ffe8e8', // 浅红
  '#fff0e0', // 浅橙
  '#fffde0', // 浅黄
  '#e8ffe8', // 浅绿
  '#e0ffff', // 浅青
  '#e8f0ff', // 浅蓝
  '#f3e8ff'  // 浅紫
]

// 随机取一个颜色
function getRandomBgColor() {
  const randomIndex = Math.floor(Math.random() * colorPool.length)
  return colorPool[randomIndex]
}

// 模拟测试收藏实例数据（仅本地调试用，正式不启用）
/*
const mockFavData = [
  {
    id: 1,
    name: '星露谷物语',
    desc: '田园农场模拟经营休闲游戏',
    favTime: Date.now() - 86400000 * 2,
    isFavorite: true
  },
  {
    id: 2,
    name: '塞尔达传说：王国之泪',
    desc: '开放世界冒险解谜大作',
    favTime: Date.now() - 86400000 * 5,
    isFavorite: true
  },
  {
    id: 3,
    name: '原神',
    desc: '二次元开放世界角色扮演游戏',
    favTime: Date.now() - 86400000 * 1,
    isFavorite: true
  },
  {
    id: 4,
    name: '空洞骑士',
    desc: '手绘风类银河恶魔城动作游戏',
    favTime: Date.now() - 86400000 * 10,
    isFavorite: true
  },
  {
    id: 5,
    name: '我的世界',
    desc: '自由沙盒创造生存游戏',
    favTime: Date.now() - 86400000 * 15,
    isFavorite: true
  },
  {
    id: 6,
    name: '双人成行',
    desc: '双人合作冒险解谜闯关游戏',
    favTime: Date.now() - 86400000 * 3,
    isFavorite: true
  },
  {
    id: 7,
    name: '只狼：影逝二度',
    desc: '高难度日式动作格斗游戏',
    favTime: Date.now() - 86400000 * 7,
    isFavorite: true
  },
  {
    id: 8,
    name: '动物森友会',
    desc: '治愈系岛屿生活模拟游戏',
    favTime: Date.now() - 86400000 * 4,
    isFavorite: true
  }
]
*/

// 加载收藏数据，请求后端真实接口
const loadData = async () => {
  // 注释mock数据，使用后端接口
  // list.value = mockFavData.map(item => ({ ...item, bgColor: getRandomBgColor() }))
  // total.value = mockFavData.length

  // 启用真实后端分页接口
  const res = await getFavoriteList(page.value, pageSize);
  list.value = res.data.list.map(item => ({ ...item, bgColor: getRandomBgColor() }));
  total.value = res.data.total;
};

// 取消收藏：调用后端删除接口，完成后重新拉取列表
const removeFav = async (gameId) => {
  // 不再前端本地过滤数据
  // list.value = list.value.filter(item => item.id !== gameId)
  // total.value = list.value.length

  // 调用后端删除收藏接口
  await delFavorite(gameId);
  // 删除成功后刷新当前页数据
  loadData();
};

watch(page, loadData)
onMounted(loadData)
</script>

<style scoped>
/* 页面整体居中容器 */
.page-favorite {
  max-width: 1300px;
  margin: 0 auto;
  padding: 32px 20px;
  min-height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
}

/* 标题居中 */
.page-title {
  text-align: center;
  color: #2c3e50;
  font-size: 26px;
  margin-bottom: 30px;
  font-weight: 600;
}

/* 空状态居中 */
.empty-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.empty-text {
  font-size: 17px;
  color: #888;
}

/* 自适应网格布局，自动居中 */
.game-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
  width: 100%;
  margin-bottom: 40px;
}

/* 单条收藏卡片样式优化，去掉固定白色背景 */
.fav-item {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: 0.2s ease;
}
.fav-item:hover {
  box-shadow: 0 4px 14px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.item-footer {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.fav-time {
  font-size: 13px;
  color: #6b7280;
}
.cancel-btn {
  width: fit-content;
  padding: 5px 14px;
  border: 1px solid #ef4444;
  background: #fff;
  color: #ef4444;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.2s;
}
.cancel-btn:hover {
  background-color: #ef4444;
  color: white;
}

/* 分页：最底部、水平居中 */
.pagination {
  margin-top: auto;
  padding-top: 20px;
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: center;
}
.pagination button {
  padding: 6px 18px;
  border: 1px solid #3b82f6;
  background: #fff;
  color: #3b82f6;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.2s;
}
.pagination button:hover:not(:disabled) {
  background-color: #3b82f6;
  color: white;
}
.pagination button:disabled {
  border-color: #cbd5e1;
  color: #94a3b8;
  cursor: not-allowed;
}
.page-num {
  font-size: 15px;
  color: #333;
}
</style>
