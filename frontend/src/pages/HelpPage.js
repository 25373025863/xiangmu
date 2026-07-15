export function HelpPage() {
  return {
    html: `
      <section class="page page--narrow">
        <div class="page-heading"><div><p class="eyebrow">帮助与状态</p><h1>项目模块状态</h1></div></div>
        <div class="status-list">
          <div><strong>偏好与 Steam</strong><span class="status status--done">已迁移</span></div>
          <div><strong>游戏数据与详情</strong><span class="status status--done">已迁移</span></div>
          <div><strong>AI 与 Key 设置</strong><span class="status status--done">已迁移</span></div>
          <div><strong>推荐结果</strong><span class="status status--done">已迁移</span></div>
          <div><strong>首页</strong><span class="status status--done">已迁移</span></div>
          <div><strong>收藏与历史</strong><span class="status status--done">已迁移</span></div>
          <div><strong>测试与部署</strong><span class="status status--partial">待补全</span></div>
        </div>
        <p class="muted">更详细的缺口和验收标准见 docs/status.md。</p>
      </section>`
  }
}
