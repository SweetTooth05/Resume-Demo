export function formatAUD(amount: number, opts?: { compact?: boolean; signed?: boolean }): string {
  const abs = Math.abs(amount)
  const prefix = opts?.signed ? (amount >= 0 ? '+' : '-') : amount < 0 ? '-' : ''

  if (opts?.compact) {
    if (abs >= 1_000_000) return `${prefix}$${(abs / 1_000_000).toFixed(2)}M`
    if (abs >= 1_000)     return `${prefix}$${(abs / 1_000).toFixed(1)}k`
  }

  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(amount)).replace('A$', prefix + '$')
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-AU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}

export function formatDateShort(date: Date): string {
  return new Intl.DateTimeFormat('en-AU', {
    day: '2-digit',
    month: 'short',
  }).format(date)
}

export function formatPercent(value: number, opts?: { signed?: boolean; decimals?: number }): string {
  const decimals = opts?.decimals ?? 2
  const prefix = opts?.signed && value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(decimals)}%`
}

export function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60_000)
  const diffHours = Math.floor(diffMs / 3_600_000)
  const diffDays = Math.floor(diffMs / 86_400_000)

  if (diffMins < 1)    return 'just now'
  if (diffMins < 60)   return `${diffMins}m ago`
  if (diffHours < 24)  return `${diffHours}h ago`
  if (diffDays < 7)    return `${diffDays}d ago`
  return formatDate(date)
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat('en-AU').format(n)
}
