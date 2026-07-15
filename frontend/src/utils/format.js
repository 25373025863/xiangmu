export function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  })[character])
}

export function joinText(values = []) {
  return values.length ? values.join(' / ') : '未注明'
}
