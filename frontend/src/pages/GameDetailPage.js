import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

import { GameApiError, getGameDetail } from '../api/gameApi'
import '../styles/gameDetail.css'

export default function GameDetailPage() {
  const { gameId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [game, setGame] = useState(null)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)
  const [imageFailed, setImageFailed] = useState(false)
  const [requestVersion, setRequestVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setStatus('loading')
    setError(null)
    setImageFailed(false)

    getGameDetail(gameId, controller.signal)
      .then((detail) => {
        setGame(detail)
        setStatus('ready')
      })
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') {
          setError(requestError)
          setStatus('error')
        }
      })

    return () => controller.abort()
  }, [gameId, requestVersion])

  const recommendationReason = location.state?.recommendationReason
    || sessionStorage.getItem(`recommendation-reason:${gameId}`)

  function goBack() {
    if (window.history.length > 1) navigate(-1)
    else navigate('/')
  }

  if (status === 'loading') {
    return <main className="detail-state"><p>正在加载游戏详情...</p></main>
  }

  if (status === 'error') {
    const notFound = error instanceof GameApiError && error.status === 404
    return (
      <main className="detail-state">
        <h1>{notFound ? '未找到这款游戏' : '游戏详情暂时无法加载'}</h1>
        <p>{notFound ? '请检查游戏 ID 是否正确。' : error?.message}</p>
        <div className="detail-state-actions">
          {!notFound && <button type="button" onClick={() => setRequestVersion((value) => value + 1)}>重试</button>}
          <button type="button" onClick={goBack}>返回上一页</button>
        </div>
      </main>
    )
  }

  return (
    <main className="game-detail-page">
      <button className="back-button" type="button" onClick={goBack}>返回上一页</button>

      <section className="game-detail-hero" aria-labelledby="game-title">
        {game.cover && !imageFailed
          ? <img className="game-detail-cover" src={game.cover} alt={`${game.title} 游戏封面`} onError={() => setImageFailed(true)} />
          : <div className="game-cover-fallback">{game.title}</div>}
        <div>
          <p className="detail-eyebrow">游戏详情</p>
          <h1 id="game-title">{game.title}</h1>
          <div className="game-facts">
            {game.score !== null && game.score !== undefined && <span>评分 {game.score}/10</span>}
            {game.price && <span>{game.price}</span>}
            {game.releaseDate && <span>{game.releaseDate}</span>}
          </div>
          <ul className="detail-tags" aria-label="游戏标签">
            {game.tags.map((tag) => <li key={tag}>{tag}</li>)}
          </ul>
        </div>
      </section>

      <div className="game-detail-layout">
        <section className="detail-section detail-description">
          <h2>游戏简介</h2>
          <p>{game.description}</p>
        </section>
        <aside className="detail-section detail-meta" aria-label="游戏基本资料">
          <dl>
            <div><dt>平台</dt><dd>{game.platforms.join('、') || '暂无信息'}</dd></div>
            <div><dt>类型</dt><dd>{game.genres.join('、') || '暂无信息'}</dd></div>
            {game.developer && <div><dt>开发商</dt><dd>{game.developer}</dd></div>}
          </dl>
        </aside>
        <section className="detail-section detail-audience">
          <h2>适合人群</h2>
          <ul>{game.suitableFor.map((person) => <li key={person}>{person}</li>)}</ul>
        </section>
        {recommendationReason && (
          <section className="detail-section detail-reason">
            <h2>推荐理由</h2>
            <p>{recommendationReason}</p>
          </section>
        )}
      </div>

      {game.purchaseUrl && (
        <a className="purchase-link" href={game.purchaseUrl} target="_blank" rel="noreferrer">
          前往购买或了解更多
        </a>
      )}
    </main>
  )
}
