import { TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '../../lib/cn'
import { formatAUD, formatPercent } from '../../lib/formatters'
import { Skeleton } from '../common/SkeletonLoader'

interface NetWorthCardProps {
  totalAUD: number
  changeAmount: number
  changePct: number
  changePeriod: 'today' | '7d' | '30d'
  breakdown: { label: string; amountAUD: number; colorClass: string }[]
  isLoading?: boolean
}

export function NetWorthCard({
  totalAUD, changeAmount, changePct, changePeriod,
  breakdown, isLoading,
}: NetWorthCardProps) {
  const isPositive = changeAmount >= 0

  return (
    <div className={cn(
      'relative col-span-12 lg:col-span-7 rounded-lg bg-navy-800',
      'border border-navy-600/40 shadow-md shadow-card-inner p-6 overflow-hidden',
    )}>
      {/* Background glow */}
      <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full bg-emerald-600/10 blur-3xl pointer-events-none" />

      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-xs font-medium text-navy-300 uppercase tracking-wider mb-2">
              Net Worth
            </p>
            {isLoading ? (
              <Skeleton className="h-12 w-56" />
            ) : (
              <p className="font-mono text-5xl font-bold text-white tabular-nums tracking-tight">
                {formatAUD(totalAUD, { compact: false })}
              </p>
            )}
          </div>

          {/* Period badge */}
          <div className="text-xs text-navy-400 bg-navy-700/60 px-2.5 py-1 rounded-md border border-navy-600/40 capitalize">
            {changePeriod === 'today' ? 'Today' : changePeriod === '7d' ? 'Past 7 days' : 'Past 30 days'}
          </div>
        </div>

        {/* Change indicator */}
        {!isLoading && (
          <div className={cn(
            'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-medium border mb-6',
            isPositive
              ? 'bg-emerald-600/15 text-emerald-400 border-emerald-600/20'
              : 'bg-rose-600/15 text-rose-400 border-rose-600/20'
          )}>
            {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            <span className="font-mono tabular-nums">
              {formatAUD(changeAmount, { signed: true })}
            </span>
            <span className="text-xs opacity-75">
              ({formatPercent(changePct, { signed: true })})
            </span>
          </div>
        )}

        {/* Breakdown bars */}
        <div className="flex flex-col gap-2">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-2 flex-1 rounded-full" />
                <Skeleton className="h-3 w-16" />
              </div>
            ))
          ) : (
            breakdown.map((item) => {
              const pct = totalAUD > 0 ? Math.abs(item.amountAUD / totalAUD) * 100 : 0
              return (
                <div key={item.label} className="flex items-center gap-3">
                  <span className="text-xs text-navy-300 w-20 flex-shrink-0">{item.label}</span>
                  <div className="flex-1 h-1.5 rounded-full bg-navy-700">
                    <div
                      className={cn('h-1.5 rounded-full transition-all duration-700', item.colorClass)}
                      style={{ width: `${Math.min(pct, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono tabular-nums text-navy-200 w-24 text-right">
                    {formatAUD(item.amountAUD, { compact: true })}
                  </span>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
