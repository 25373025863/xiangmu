import { Navigate, createBrowserRouter } from 'react-router-dom'

import GameDetailPage from '../pages/GameDetailPage'

const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/games/g003" replace /> },
  { path: '/games/:gameId', element: <GameDetailPage /> }
])

export default router
