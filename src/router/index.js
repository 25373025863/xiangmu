import { createRouter, createWebHistory } from 'vue-router'
// 下面这行注释掉，HomePage文件不存在，不能导入
// import HomePage from '../pages/HomePage.vue'
import FavoritePage from '../pages/FavoritePage.vue'
import HistoryPage from '../pages/HistoryPage.vue'

const routes = [
    { path: '/', redirect: '/favorite' },
    { path: '/favorite', component: FavoritePage },
    { path: '/history', component: HistoryPage }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router