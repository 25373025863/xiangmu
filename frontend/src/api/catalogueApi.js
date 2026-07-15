import { apiRequest } from './request.js'

export function getCatalogueGames({ keyword = '', sort = 'topsellers', page = 1, size = 12 } = {}, options = {}) {
  const query = new URLSearchParams({
    keyword: String(keyword),
    sort: String(sort),
    page: String(page),
    size: String(size)
  })

  return apiRequest(`/api/catalogue/games?${query.toString()}`, options)
}
