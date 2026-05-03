import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAppStore } from './stores/appStore'
import { AppLayout } from './components/layout/AppLayout'
import { Dashboard } from './pages/Dashboard'
import { Chat } from './pages/Chat'
import { Transactions } from './pages/Transactions'
import { Portfolio } from './pages/Portfolio'
import { Recommendations } from './pages/Recommendations'
import { Settings } from './pages/Settings'
import { Onboarding } from './pages/Onboarding'

export default function App() {
  const { onboardingComplete, theme } = useAppStore()

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  return (
    <div data-theme={theme} className="h-full w-full min-h-0">
      <BrowserRouter>
        <Routes>
          <Route path="/onboarding" element={<Onboarding />} />

          {!onboardingComplete ? (
            <Route path="*" element={<Navigate to="/onboarding" replace />} />
          ) : (
            <Route element={<AppLayout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard"        element={<Dashboard />} />
              <Route path="/chat"             element={<Chat />} />
              <Route path="/transactions"     element={<Transactions />} />
              <Route path="/portfolio"        element={<Portfolio />} />
              <Route path="/recommendations"  element={<Recommendations />} />
              <Route path="/settings"         element={<Settings />} />
              <Route path="*"                 element={<Navigate to="/dashboard" replace />} />
            </Route>
          )}
        </Routes>
      </BrowserRouter>
    </div>
  )
}
