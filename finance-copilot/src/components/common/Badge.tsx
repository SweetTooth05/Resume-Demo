import { cn } from '../../lib/cn'

type BadgeVariant = 'emerald' | 'rose' | 'amber' | 'navy' | 'blue' | 'purple'

interface BadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  className?: string
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  emerald: 'bg-emerald-600/15 text-emerald-400 border-emerald-600/25',
  rose:    'bg-rose-600/15 text-rose-400 border-rose-600/25',
  amber:   'bg-amber-600/15 text-amber-400 border-amber-600/25',
  navy:    'bg-navy-700/50 text-navy-300 border-navy-600/40',
  blue:    'bg-blue-600/15 text-blue-400 border-blue-600/25',
  purple:  'bg-purple-600/15 text-purple-400 border-purple-600/25',
}

export function Badge({ children, variant = 'navy', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
        VARIANT_CLASSES[variant],
        className
      )}
    >
      {children}
    </span>
  )
}

export function LocalBadge() {
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-600/10 border border-emerald-600/20">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 motion-safe:animate-pulse" />
      <span className="text-2xs font-semibold text-emerald-400 uppercase tracking-wider">All Local</span>
    </div>
  )
}
