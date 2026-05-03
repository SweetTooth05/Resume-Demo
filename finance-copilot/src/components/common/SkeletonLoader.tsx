import { cn } from '../../lib/cn'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'skeleton-shimmer rounded-md',
        className
      )}
    />
  )
}

export function SkeletonCard() {
  return (
    <div className="p-5 rounded-lg bg-navy-800 border border-navy-600/40 flex flex-col gap-3">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-8 w-36" />
      <Skeleton className="h-3 w-20" />
    </div>
  )
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 px-4 py-3 border-b border-navy-700/50">
      <Skeleton className="h-7 w-7 rounded-md" />
      <div className="flex-1 flex flex-col gap-1.5">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-3 w-20" />
      </div>
      <Skeleton className="h-4 w-16" />
      <Skeleton className="h-5 w-20 rounded-sm" />
      <Skeleton className="h-4 w-20" />
    </div>
  )
}
