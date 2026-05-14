import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ClientDetail from './pages/ClientDetail'
import PFICWorkspace from './pages/PFICWorkspace'
import UserManual from './pages/UserManual'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/clients/:clientId" element={<ClientDetail />} />
        <Route path="/holdings/:holdingId" element={<PFICWorkspace />} />
        <Route path="/manual" element={<UserManual />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
