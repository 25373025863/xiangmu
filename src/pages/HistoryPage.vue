<template>
  <div class="page-history">
    <!-- 标题右偏移 -->
    <h2 class="page-title">历史记录</h2>

    <div v-if="history.length === 0" class="empty-wrap">
      <p class="empty-text">暂无推荐历史记录</p>
    </div>

    <div v-else class="history-list">
      <!-- 绑定随机背景色 -->
      <div
          class="history-item"
          v-for="record in history"
          :key="record.id"
          :style="{ backgroundColor: record.bgColor }"
      >
        <div class="history-head">
          <span>生成时间：{{ formatTime(record.createTime) }}</span>
          <h4>你的偏好设置：</h4>
          <p>{{ formatPreference(record.preference) }}</p>
        </div>
        <div class="history-games">
          <h4>本次推荐游戏：</h4>
          <div class="card-wrap">
            <GameCard
                v-for="game in record.games"
                :key="game.id"
                :game="game"
                :is-favorite="game.isFavorite"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 分页底部居中，动态页码 第x/总页数 -->
    <div class="pagination">
      <button :disabled="page <= 1" @click="page--">上一页</button>
      <span class="page-text">第 {{ page }} / {{ totalPage }} 页</span>
      <button :disabled="page * pageSize >= total" @click="page++">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import GameCard from '../components/GameCard.vue';
import { getHistoryList } from '../api/recommendApi';
import { formatTime } from '../utils/format';

const history = ref([]);
const page = ref(1);
const pageSize = 10;
const total = ref(0);

// 计算总页数，动态更新分母
const totalPage = computed(() => Math.ceil(total.value / pageSize));

// 红橙黄绿青蓝紫 低饱和浅背景色池
const colorPool = [
  '#ffe8e8', // 浅红
  '#fff0e0', // 浅橙
  '#fffde0', // 浅黄
  '#e8ffe8', // 浅绿
  '#e0ffff', // 浅青
  '#e8f0ff', // 浅蓝
  '#f3e8ff'  // 浅紫
]
// 随机取色
function getRandomBgColor() {
  const idx = Math.floor(Math.random() * colorPool.length)
  return colorPool[idx]
}

// 将type/maxPrice/style转换为中文标签
function formatPreference(obj) {
  const nameMap = {
    type: '类型',
    maxPrice: '价格',
    style: '风格'
  }
  const list = []
  for (const key in obj) {
    list.push(`${nameMap[key]}：${obj[key]}`)
  }
  return list.join('，')
}

// 模拟历史测试数据
const mockHistoryData = [
  {
    id: 1,
    createTime: Date.now() - 86400000 * 1,
    preference: { type: '休闲', maxPrice: 100, style: '治愈' },
    games: [
      { id: 1, name: '星露谷物语', desc: '田园农场模拟经营', isFavorite: true },
      { id: 2, name: '动物森友会', desc: '岛屿治愈生活', isFavorite: false }
    ]
  },
  {
    id: 2,
    createTime: Date.now() - 86400000 * 3,
    preference: { type: '动作', maxPrice: 200, style: '硬核' },
    games: [
      { id: 3, name: '只狼', desc: '高难度武士动作游戏', isFavorite: true },
      { id: 4, name: '空洞骑士', desc: '手绘类魂闯关', isFavorite: true }
    ]
  },
  {
    id: 3,
    createTime: Date.now() - 86400000 * 5,
    preference: { type: '开放世界', maxPrice: 300, style: '奇幻' },
    games: [
      { id: 5, name: '塞尔达王国之泪', desc: '自由开放冒险', isFavorite: true },
      { id: 6, name: '原神', desc: '二次元开放世界', isFavorite: false }
    ]
  }
]

const loadHistory = async () => {
  // 给每条历史记录附加随机背景色
  history.value = mockHistoryData.map(item => ({
    ...item,
    bgColor: getRandomBgColor()
  }))
  total.value = mockHistoryData.length

  // 后端真实接口（正式上线打开注释）
  // const res = await getHistoryList(page.value, pageSize);
  // history.value = res.data.list.map(item => ({ ...item, bgColor: getRandomBgColor() }));
  // total.value = res.data.total;
};

watch(page, loadHistory);
onMounted(loadHistory);
</script>

<style scoped>
.page-history {
  max-width: 1300px;
  margin: 0 auto;
  padding: 32px 20px;
  min-height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
}

/* 标题向右偏移 */
.page-title {
  margin-left: 60px;
  color: #2c3e50;
  font-size: 26px;
  margin-bottom: 30px;
  font-weight: 600;
}

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

.history-list {
  flex: 1;
  margin-bottom: 40px;
}
.history-item {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  margin-bottom: 20px;
  /* 删除固定白色背景，由随机色控制 */
}
.history-head {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}
.history-head h4 {
  margin: 8px 0 4px;
  color: #444;
}
.history-head span {
  font-size: 14px;
  color: #666;
}
.history-head p {
  color: #777;
  font-size: 14px;
}

.card-wrap {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
  margin-top: 10px;
}

/* 分页底部居中 */
.pagination {
  margin-top: auto;
  padding-top: 20px;
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: center;
}
.pagination button {
  padding: 6px 20px;
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
.page-text {
  font-size: 16px;
  color: #222;
  font-weight: 500;
}
</style>