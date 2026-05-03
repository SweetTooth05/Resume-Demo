import { TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '../lib/cn'
import { formatAUD, formatPercent } from '../lib/formatters'
import { MetricCard } from '../components/cards/MetricCard'
import { MOCK_HOLDINGS } from '../lib/mockData'

function Sparkline({ trend }: { trend: 'up' | 'down' }) {
  const points = trend === 'up'
    ? '0,16 8,12 16,14 24,8 32,10 40,4 48,6 56,2'
    : '0,4 8,6 16,4 24,10 32,8 40,12 48,10 56,16'
  const color = trend === 'up' ? '#12c97d' : '#e11d48'

  return (
    <svg width="56" height="20" className="flex-shrink-0">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function Portfolio() {
  const totalValue = MOCK_HOLDINGS.reduce((s, h) => s + h.marketValueAUD, 0)
  const totalGain = MOCK_HOLDINGS.reduce((s, h) => s + h.unrealisedPnL, 0)
  const totalCost = MOCK_HOLDINGS.reduce((s, h) => s + h.units * h.avgCostBasis, 0)
  const totalGainPct = totalCost > 0 ? (totalGain / totalCost) * 100 : 0

  return (
    <div className="h-full overflow-y-auto p-6">
      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="Portfolio Value"
          value={totalValue}
          format="currency"
          variant="default"
        />
        <MetricCard
          title="Total Gain"
          value={totalGain}
          format="currency"
          trend={totalGain >= 0 ? 'up' : 'down'}
          variant={totalGain >= 0 ? 'positive' : 'negative'}
        />
        <MetricCard
          title="Gain %"
          value={totalGainPct}
          format="percent"
          trend={totalGainPct >= 0 ? 'up' : 'down'}
          variant={totalGainPct >= 0 ? 'positive' : 'negative'}
        />
        <MetricCard
          title="Holdings"
          value={MOCK_HOLDINGS.length}
          format="number"
        />
      </div>

      {/* Holdings table */}
      <div className="rounded-lg bg-navy-800 border border-navy-600/40 shadow-sm shadow-card-inner overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-navy-700 border-b border-navy-600/60">
              {['Ticker', 'Name', 'Units', 'Avg Cost', 'Current', 'Market Value', 'P&L', 'P&L %', 'Alloc %', 'Trend'].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-navy-300 uppercase tracking-wider whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {MOCK_HOLDINGS.map(h => {
              const todayChange = h.currentPrice - h.previousClose
              const trend = todayChange >= 0 ? 'up' : 'down'
              return (
                <tr key={h.ticker} className="border-b border-navy-700/50 hover:bg-navy-800/60 transition-colors duration-100">
                  <td className="px-4 py-3">
                    <span className="text-sm font-semibold text-white font-mono">{h.ticker}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-navy-300 max-w-[160px] truncate block">{h.name}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm font-mono tabular-nums text-navy-200">{h.units}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm font-mono tabular-nums text-navy-300">{formatAUD(h.avgCostBasis)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col">
                      <span className="text-sm font-mono tabular-nums text-white font-medium">{formatAUD(h.currentPrice)}</span>
                      <span className={cn(
                        'text-xs font-mono tabular-nums',
                        todayChange >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      )}>
                        {formatAUD(todayChange, { signed: true })}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm font-mono tabular-nums text-white font-medium">{formatAUD(h.marketValueAUD)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn(
                      'text-sm font-mono tabular-nums font-medium',
                      h.unrealisedPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    )}>
                      {formatAUD(h.unrealisedPnL, { signed: true })}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className={cn(
                      'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border',
                      h.unrealisedPnLPct >= 0
                        ? 'bg-emerald-600/15 text-emerald-400 border-emerald-600/20'
                        : 'bg-rose-600/15 text-rose-400 border-rose-600/20'
                    )}>
                      {h.unrealisedPnLPct >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                      {formatPercent(h.unrealisedPnLPct, { signed: true })}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 rounded-full bg-navy-700">
                        <div
                          className="h-1.5 rounded-full bg-indigo-400 transition-all duration-500"
                          style={{ width: `${h.allocationPct}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono tabular-nums text-navy-300 w-10">
                        {formatPercent(h.allocationPct, { decimals: 1 })}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Sparkline trend={trend} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
