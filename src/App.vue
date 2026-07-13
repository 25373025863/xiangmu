<script setup>
// 移除原来HelloWorld、TheWelcome的导入，只保留路由组件
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <!-- 导航跳转 -->
    <nav class="nav-bar">
      <router-link to="/favorite">我的收藏</router-link>
      <router-link to="/history">历史记录</router-link>
    </nav>
    <router-view />
  </div>
</template>

<style scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
}
.nav-bar {
  padding: 16px 20px;
  background: #f5f5f5;
  gap: 20px;
  display: flex;
}
.nav-bar a {
  text-decoration: none;
  color: #333;
  font-size: 16px;
}
.nav-bar a.router-link-active {
  color: #42b983;
  font-weight: bold;
}
</style>