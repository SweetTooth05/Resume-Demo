import {
  LayoutDashboard, MessageSquare, ArrowLeftRight,
  LineChart, Lightbulb, Settings, ChevronLeft,
  ChevronRight, Cpu, RefreshCw, AlertCircle,
} from 'lucide-react'
import { cn } from '../../lib/cn'
import type { NavRoute } from '../../types'
import { formatRelativeTime } from '../../lib/formatters'

interface NavItem {
  id: NavRoute
  label: string
  icon: React.FC<{ className?: string; size?: number }>
  badge?: number
}

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  currentRoute: NavRoute
  onNavigate: (route: NavRoute) => void
  modelTier: string
  syncStatus: 'idle' | 'syncing' | 'error' | 'never'
  lastSyncTime?: Date
}

const NAV_ITEMS: NavItem[] = [
  { id: '/dashboard',        label: 'Dashboard',        icon: LayoutDashboard },
  { id: '/chat',             label: 'Chat',             icon: MessageSquare   },
  { id: '/transactions',     label: 'Transactions',     icon: ArrowLeftRight  },
  { id: '/portfolio',        label: 'Portfolio',        icon: LineChart       },
  { id: '/recommendations',  label: 'Recommendations',  icon: Lightbulb, badge: 3 },
  { id: '/settings',         label: 'Settings',         icon: Settings        },
]

export function Sidebar({
  collapsed, onToggle, currentRoute, onNavigate,
  modelTier, syncStatus, lastSyncTime,
}: SidebarProps) {
  return (
    <aside
      className={cn(
        'flex flex-col flex-shrink-0 bg-[var(--surface-raised)] border-r border-[var(--surface-border)]',
        'transition-[width] duration-300 ease-in-out overflow-hidden z-40',
        collapsed ? 'w-16' : 'w-72'
      )}
      aria-label="Main navigation"
    >
      {/* Header */}
      <div className={cn(
        'flex items-center border-b border-[var(--surface-border)] px-3',
        collapsed ? 'h-14 justify-center' : 'h-14 justify-between px-4'
      )}>
        {!collapsed && (
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-lg bg-emerald-600/20 border border-emerald-600/30 flex items-center justify-center shadow-sm">
              <LineChart size={14} className="text-emerald-400" aria-hidden />
            </div>
            <span className="text-sm font-semibold text-[var(--text-primary)] tracking-tight truncate">Finance Copilot</span>
          </div>
        )}
        {collapsed && (
          <div className="w-7 h-7 rounded-lg bg-emerald-600/20 border border-emerald-600/30 flex items-center justify-center shadow-sm" title="Finance Copilot">
            <LineChart size={14} className="text-emerald-400" aria-hidden />
          </div>
        )}
        {!collapsed && (
          <button
            type="button"
            onClick={onToggle}
            aria-label="Collapse sidebar"
            className="p-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] transition-colors duration-150"
          >
            <ChevronLeft size={16} aria-hidden />
          </button>
        )}
      </div>

      {/* Nav items */}
      <nav className="flex-1 py-2 overflow-y-auto" aria-label="Primary">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          const isActive = currentRoute === item.id
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              title={collapsed ? item.label : undefined}
              aria-label={collapsed ? item.label : undefined}
              aria-current={isActive ? 'page' : undefined}
              className={cn(
                'w-full flex items-center gap-3 mx-2 my-0.5 px-3 py-2.5 rounded-lg text-left relative',
                'transition-colors duration-150 border border-transparent',
                collapsed ? 'w-10 mx-3 justify-center px-0' : 'w-[calc(100%-16px)]',
                isActive
                  ? cn(
                      'text-[var(--text-primary)] bg-[var(--surface-elevated)] border-[var(--surface-border)] shadow-card-inner',
                      !collapsed &&
                        'before:absolute before:left-1.5 before:top-1/2 before:-translate-y-1/2 before:h-7 before:w-0.5 before:rounded-full before:bg-emerald-500 before:content-[""]',
                    )
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-elevated)]',
              )}
            >
              <Icon
                size={18}
                className={cn(
                  'flex-shrink-0 transition-colors duration-150',
                  isActive ? 'text-emerald-400' : 'text-current'
                )}
              />
              {!collapsed && (
                <>
                  <span className="text-sm font-medium flex-1 truncate">{item.label}</span>
                  {item.badge && item.badge > 0 && (
                    <span className="px-1.5 py-0.5 text-2xs font-semibold rounded-full bg-emerald-600/20 text-emerald-400 tabular-nums">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer — sync status + model tier */}
      <div className={cn(
        'border-t border-[var(--surface-border)] p-3 flex flex-col gap-2 bg-[color-mix(in_srgb,var(--surface-base)_35%,transparent)]',
        collapsed && 'items-center'
      )}>
        {/* Sync status */}
        <div className={cn(
          'flex items-center gap-2',
          collapsed && 'justify-center'
        )}>
          {syncStatus === 'syncing' && (
            <RefreshCw size={13} className="text-amber-400 animate-spin" />
          )}
          {syncStatus === 'error' && (
            <AlertCircle size={13} className="text-rose-400" />
          )}
          {(syncStatus === 'idle' || syncStatus === 'never') && (
            <span className="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0" />
          )}
          {!collapsed && (
            <span className="text-xs text-[var(--text-muted)]">
              {syncStatus === 'syncing' && 'Syncing...'}
              {syncStatus === 'error' && 'Sync failed'}
              {syncStatus === 'idle' && lastSyncTime && `Synced ${formatRelativeTime(lastSyncTime)}`}
              {syncStatus === 'never' && 'Not synced'}
            </span>
          )}
        </div>

        {/* Model tier */}
        {!collapsed && (
          <div className="flex items-center gap-2">
            <Cpu size={13} className="text-[var(--text-muted)] flex-shrink-0" />
            <span className="text-xs text-[var(--text-muted)]">Qwen {modelTier} · Local</span>
          </div>
        )}

        {/* Expand button when collapsed */}
        {collapsed && (
          <button
            type="button"
            onClick={onToggle}
            aria-label="Expand sidebar"
            className="p-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] transition-colors duration-150 mt-1"
          >
            <ChevronRight size={16} aria-hidden />
          </button>
        )}
      </div>
    </aside>
  )
}
