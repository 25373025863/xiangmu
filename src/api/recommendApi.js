// 基础请求封装，项目通用
const baseUrl = '/api';

// 收藏接口
export function addFavorite(gameId) {
    return fetch(`${baseUrl}/favorite/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gameId })
    }).then(res => res.json());
}

export function delFavorite(gameId) {
    return fetch(`${baseUrl}/favorite/${gameId}`, {
        method: 'DELETE'
    }).then(res => res.json());
}

export function getFavoriteList(page = 1, size = 10) {
    return fetch(`${baseUrl}/favorite/list?page=${page}&size=${size}`)
        .then(res => res.json());
}

// 历史记录接口
export function getHistoryList(page = 1, size = 10) {
    return fetch(`${baseUrl}/history/list?page=${page}&size=${size}`)
        .then(res => res.json());
}