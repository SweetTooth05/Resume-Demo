import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '../../lib/cn'
import { formatAUD, formatPercent } from '../../lib/formatters'
import { Skeleton } from '../common/SkeletonLoader'

interface MetricCardProps {
  title: string
  value: number | string
  format?: 'currency' | 'percent' | 'number' | 'text'
  trend?: 'up' | 'down' | 'flat'
  trendValue?: number
  trendLabel?: string
  icon?: React.FC<{ className?: string; size?: number }>
  variant?: 'default' | 'positive' | 'negative' | 'warning'
  isLoading?: boolean
  onClick?: () => void
  className?: string
}

export function MetricCard({
  title, value, format = 'text',
  trend, trendValue, trendLabel,
  icon: Icon, variant = 'default',
  isLoading, onClick, className,
}: MetricCardProps) {
  const formatted = isLoading ? '' : format === 'currency'
    ? formatAUD(value as number)
    : format === 'percent'
    ? formatPercent(value as number)
    : String(value)

  return (
    <div
      onClick={onClick}
      className={cn(
        'flex flex-col gap-3 p-5 rounded-lg bg-navy-800',
        'border border-navy-600/40 shadow-sm shadow-card-inner',
        'transition-all duration-200',
        onClick && 'cursor-pointer hover:border-navy-500/60 hover:bg-navy-750',
        variant === 'positive' && 'border-emerald-600/25',
        variant === 'negative' && 'border-rose-600/25',
        variant === 'warning'  && 'border-amber-600/25',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-navy-300 uppercase tracking-wider">
          {title}
        </span>
        {Icon && (
          <Icon size={16} className="text-navy-400" />
        )}
      </div>

      {isLoading ? (
        <>
          <Skeleton className="h-8 w-36" />
          <Skeleton className="h-3 w-20" />
        </>
      ) : (
        <>
          <span className={cn(
            'text-2xl font-semibold font-mono tabular-nums text-white',
            variant === 'positive' && 'text-emerald-400',
            variant === 'negative' && 'text-rose-400',
          )}>
            {formatted}
          </span>

          {trend && (
            <div className={cn(
              'flex items-center gap-1 text-xs',
              trend === 'up'   && 'text-emerald-400',
              trend === 'down' && 'text-rose-400',
              trend === 'flat' && 'text-navy-400',
            )}>
              {trend === 'up'   && <TrendingUp size={12} />}
              {trend === 'down' && <TrendingDown size={12} />}
              {trend === 'flat' && <Minus size={12} />}
              {trendValue !== undefined && (
                <span>{formatPercent(trendValue, { signed: true })}</span>
              )}
              {trendLabel && <span className="text-navy-400">{trendLabel}</span>}
            </div>
          )}
        </>
      )}
    </div>
  )
}
