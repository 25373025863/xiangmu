import { useNavigate } from 'react-router-dom'

export default function GameCard({ game }) {
  const navigate = useNavigate()
  const gameId = game.gameId || game.game_id || game.id
  const recommendationReason = game.recommendationReason || game.reason
  const title = game.title || game.name || '未命名游戏'
  const description = recommendationReason || game.description || game.desc || ''

  function openDetail() {
    if (!gameId) return
    if (recommendationReason) {
      sessionStorage.setItem(`recommendation-reason:${gameId}`, recommendationReason)
    }
    navigate(`/games/${encodeURIComponent(gameId)}`, {
      state: { recommendationReason }
    })
  }

  return (
    <article className="game-card">
      <h3>{title}</h3>
      <p>{description}</p>
      <button type="button" onClick={openDetail}>查看详情</button>
    </article>
  )
}
