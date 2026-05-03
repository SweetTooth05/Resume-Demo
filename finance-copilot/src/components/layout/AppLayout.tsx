import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { Sidebar } from '../navigation/Sidebar'
import { LocalBadge } from '../common/Badge'
import { useAppStore } from '../../stores/appStore'
import type { NavRoute } from '../../types'

export function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const {
    sidebarCollapsed, toggleSidebar, syncStatus, lastSyncTime, hardwareProfile,
  } = useAppStore()

  const currentRoute = location.pathname as NavRoute

  return (
    <div className="flex h-full w-full overflow-hidden bg-[var(--surface-base)] text-[var(--text-primary)]">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={toggleSidebar}
        currentRoute={currentRoute}
        onNavigate={(route) => navigate(route)}
        modelTier={hardwareProfile?.modelTier ?? '7B'}
        syncStatus={syncStatus}
        lastSyncTime={lastSyncTime}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="flex items-center justify-between gap-4 px-6 min-h-14 h-14 border-b border-[var(--surface-border)] bg-[color-mix(in_srgb,var(--surface-raised)_88%,transparent)] backdrop-blur-md backdrop-saturate-150 flex-shrink-0 z-30">
          <div className="min-w-0">
            <h1 className="text-[0.9375rem] font-semibold tracking-tight text-[var(--text-primary)]">
              {getPageTitle(currentRoute)}
            </h1>
            <p className="text-[11px] text-[var(--text-muted)] truncate leading-tight mt-0.5 hidden sm:block">
              {getPageSubtitle(currentRoute)}
            </p>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <LocalBadge />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function getPageTitle(route: NavRoute): string {
  const titles: Record<NavRoute, string> = {
    '/dashboard':       'Dashboard',
    '/chat':            'AI Assistant',
    '/transactions':    'Transactions',
    '/portfolio':       'Portfolio',
    '/recommendations': 'Recommendations',
    '/settings':        'Settings',
    '/onboarding':      'Setup',
  }
  return titles[route] ?? 'Finance Copilot'
}

function getPageSubtitle(route: NavRoute): string {
  const subtitles: Record<NavRoute, string> = {
    '/dashboard':       'Net worth, cashflow, and spending at a glance',
    '/chat':            'Ask questions — your data never leaves this device',
    '/transactions':    'Review and search synced account activity',
    '/portfolio':       'Holdings and allocation across accounts',
    '/recommendations': 'Prioritized actions based on your finances',
    '/settings':        'API keys, hardware, and local data',
    '/onboarding':      'Tailor insights to your situation',
  }
  return subtitles[route] ?? ''
}
