// 基础请求封装，项目通用
const baseUrl = '/api';

// 收藏接口
export function addFavorite(gameId) {
    return fetch(`${baseUrl}/favorites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_id: gameId })
    }).then(res => res.json());
}

export function delFavorite(gameId) {
    return fetch(`${baseUrl}/favorites/${gameId}`, {
        method: 'DELETE'
    }).then(res => res.json());
}

export function getFavoriteList(page = 1, size = 10) {
    return fetch(`${baseUrl}/favorites?page=${page}&size=${size}`)
        .then(res => res.json());
}

// 历史记录接口
export function getHistoryList(page = 1, size = 10) {
    return fetch(`${baseUrl}/histories?page=${page}&size=${size}`)
        .then(res => res.json());
}
