import { useState } from 'react'
import { CheckCircle2, Clock, X, ChevronDown, ChevronRight, Wrench } from 'lucide-react'
import { cn } from '../../lib/cn'
import { formatDate } from '../../lib/formatters'
import type { Recommendation, McpToolCall } from '../../types'

interface RecommendationCardProps {
  rec: Recommendation
  onAccept: (id: string) => void
  onSnooze: (id: string, until: Date) => void
  onDismiss: (id: string) => void
}

const CATEGORY_ICONS: Record<string, string> = {
  savings:   '💰',
  spending:  '🧾',
  portfolio: '📈',
  tax:       '🏛️',
  cashflow:  '💸',
}

const PRIORITY_CLASSES = {
  high:   'bg-rose-600/15 text-rose-400 border-rose-600/25',
  medium: 'bg-amber-600/15 text-amber-400 border-amber-600/25',
  low:    'bg-navy-700/50 text-navy-300 border-navy-600/40',
}

function ToolCallPanel({ calls }: { calls: McpToolCall[] }) {
  return (
    <div className="mt-2 rounded-lg border border-navy-700/60 bg-navy-900/80 overflow-hidden animate-fade-in">
      <div className="px-3 py-2 bg-navy-850 border-b border-navy-700/60">
        <span className="text-xs font-medium text-navy-400 uppercase tracking-wider">
          Show working — {calls.length} tool call{calls.length !== 1 ? 's' : ''}
        </span>
      </div>
      {calls.map((call, i) => (
        <div key={i} className="px-3 py-2 border-b border-navy-700/40 last:border-b-0">
          <p className="text-xs font-mono text-amber-400 font-medium">{call.toolName}</p>
          <pre className="mt-1 text-xs font-mono text-navy-300 bg-navy-950/50 rounded px-2 py-1.5 overflow-x-auto">
            {JSON.stringify({ args: call.args, result: call.result }, null, 2)}
          </pre>
          <p className="mt-1 text-2xs text-navy-500">{call.durationMs}ms</p>
        </div>
      ))}
    </div>
  )
}

export function RecommendationCard({ rec, onAccept, onSnooze, onDismiss }: RecommendationCardProps) {
  const [expanded, setExpanded] = useState(false)

  const confidencePct = Math.round(rec.confidence * 100)
  const confidenceColor = rec.confidence >= 0.75 ? 'bg-emerald-500' :
                          rec.confidence >= 0.5  ? 'bg-amber-500' : 'bg-navy-500'

  const snoozeWeek = () => {
    const d = new Date()
    d.setDate(d.getDate() + 7)
    onSnooze(rec.id, d)
  }

  return (
    <div className={cn(
      'flex flex-col gap-4 p-5 rounded-lg bg-navy-800',
      'border border-navy-600/40 shadow-sm shadow-card-inner',
      'hover:border-navy-500/50 transition-all duration-200',
      rec.status !== 'pending' && 'opacity-60',
    )}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="text-lg leading-none mt-0.5">
            {CATEGORY_ICONS[rec.category] ?? '💡'}
          </span>
          <div>
            <p className="text-sm font-semibold text-white leading-tight">{rec.title}</p>
            <p className="mt-0.5 text-xs text-navy-400">{formatDate(rec.generatedAt)}</p>
          </div>
        </div>
        <span className={cn(
          'flex-shrink-0 px-2 py-0.5 rounded-full text-xs font-medium border capitalize',
          PRIORITY_CLASSES[rec.priority]
        )}>
          {rec.priority}
        </span>
      </div>

      {/* Body */}
      <p className="text-sm text-navy-200 leading-relaxed">{rec.body}</p>

      {/* Confidence */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1 rounded-full bg-navy-700">
          <div
            className={cn('h-1 rounded-full transition-all duration-500', confidenceColor)}
            style={{ width: `${confidencePct}%` }}
          />
        </div>
        <span className="text-xs text-navy-400 tabular-nums w-10 text-right">
          {confidencePct}%
        </span>
      </div>

      {/* Show working */}
      {rec.mcpCalls.length > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs text-navy-400 hover:text-navy-200 hover:bg-navy-800/50 transition-colors duration-150 w-fit"
        >
          <Wrench size={11} />
          <span>Show working</span>
          {expanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
        </button>
      )}

      {expanded && <ToolCallPanel calls={rec.mcpCalls} />}

      {/* Actions */}
      {rec.status === 'pending' && (
        <div className="flex items-center gap-2 mt-1">
          <button
            onClick={() => onAccept(rec.id)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium bg-emerald-600/15 text-emerald-400 border border-emerald-600/25 hover:bg-emerald-600/25 hover:border-emerald-500/40 transition-all duration-150 active:scale-95"
          >
            <CheckCircle2 size={14} />
            Accept
          </button>
          <button
            onClick={snoozeWeek}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium bg-navy-700 text-navy-300 border border-navy-600/50 hover:bg-navy-650 hover:text-navy-200 transition-all duration-150 active:scale-95"
          >
            <Clock size={14} />
            Snooze
          </button>
          <button
            onClick={() => onDismiss(rec.id)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium text-navy-400 hover:text-rose-400 transition-colors duration-150"
          >
            <X size={14} />
            Dismiss
          </button>
        </div>
      )}

      {rec.status !== 'pending' && (
        <p className="text-xs text-navy-500 capitalize">{rec.status}</p>
      )}
    </div>
  )
}
