import { useState, useEffect, useMemo } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import { AlertCircle, Receipt, TrendingUp, Landmark } from 'lucide-react'
import { invoke } from '@tauri-apps/api/core'
import { cn } from '../lib/cn'
import { formatAUD } from '../lib/formatters'
import { NetWorthCard } from '../components/cards/NetWorthCard'
import { MetricCard } from '../components/cards/MetricCard'
import { useAppStore } from '../stores/appStore'
import { MOCK_NET_WORTH, MOCK_CASHFLOW, MOCK_TRANSACTIONS, MOCK_RECOMMENDATIONS } from '../lib/mockData'
import type { Transaction, Recommendation } from '../types'

type Period = 'weekly' | 'monthly' | 'yearly'

const CATEGORY_COLORS_MAP: Record<string, string> = {
  groceries: '#12c97d', dining: '#f59e0b', transport: '#60a5fa',
  utilities: '#94a3b8', entertainment: '#a78bfa', other: '#475569',
  healthcare: '#34d399', shopping: '#f472b6', income: '#10b981',
}

const CASHFLOW_CHART_FALLBACK = [
  { month: 'Nov', income: 5833, expenses: 4200 },
  { month: 'Dec', income: 5833, expenses: 5100 },
  { month: 'Jan', income: 5833, expenses: 3900 },
  { month: 'Feb', income: 5833, expenses: 3750 },
  { month: 'Mar', income: 5833, expenses: 4050 },
  { month: 'Apr', income: 5833, expenses: 3813 },
]

function CashflowToggle({ period, onChange }: { period: Period; onChange: (p: Period) => void }) {
  return (
    <div className="flex items-center bg-navy-900 border border-navy-600/40 rounded-lg p-0.5">
      {(['weekly', 'monthly', 'yearly'] as Period[]).map(p => (
        <button
          key={p}
          onClick={() => onChange(p)}
          className={cn(
            'px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150 capitalize',
            period === p
              ? 'bg-navy-700 text-white shadow-sm'
              : 'text-navy-400 hover:text-navy-200'
          )}
        >
          {p}
        </button>
      ))}
    </div>
  )
}

const CUSTOM_TOOLTIP_STYLE = {
  backgroundColor: '#162140',
  border: '1px solid rgba(38,58,115,0.6)',
  borderRadius: '8px',
  fontSize: '12px',
  color: '#f0f4ff',
}

function InsightGlyph({ category }: { category: Recommendation['category'] }) {
  const Icon = category === 'spending' ? Receipt : category === 'portfolio' ? TrendingUp : Landmark
  return (
    <div className="w-8 h-8 rounded-lg bg-navy-900/80 border border-navy-600/40 flex items-center justify-center flex-shrink-0">
      <Icon size={16} className="text-emerald-400" aria-hidden />
    </div>
  )
}

function buildCategorySpend(transactions: Transaction[]) {
  const totals: Record<string, number> = {}
  for (const tx of transactions) {
    if (tx.amount < 0 && tx.category !== 'income' && tx.category !== 'transfer') {
      totals[tx.category] = (totals[tx.category] ?? 0) + Math.abs(tx.amount)
    }
  }
  return Object.entries(totals)
    .map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value: Math.round(value), color: CATEGORY_COLORS_MAP[name] ?? '#475569' }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6)
}

function buildSixMonthCashflowChart(transactions: Transaction[]) {
  const now = new Date()
  const buckets: { key: string; label: string; income: number; expenses: number }[] = []
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    const label = d.toLocaleString('en-AU', { month: 'short' })
    buckets.push({ key, label, income: 0, expenses: 0 })
  }
  for (const tx of transactions) {
    const t = new Date(tx.date)
    const key = `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}`
    const b = buckets.find((x) => x.key === key)
    if (!b) continue
    if (tx.amount > 0) b.income += tx.amount
    else b.expenses += Math.abs(tx.amount)
  }
  return buckets.map(({ label, income, expenses }) => ({ month: label, income, expenses }))
}

function buildCashflowFromTransactions(transactions: Transaction[], period: Period) {
  const now = new Date()
  let startDate: Date
  if (period === 'weekly') startDate = new Date(now.getTime() - 7 * 86400_000)
  else if (period === 'yearly') startDate = new Date(now.getFullYear(), 0, 1)
  else startDate = new Date(now.getFullYear(), now.getMonth(), 1)

  let income = 0, expenses = 0
  for (const tx of transactions) {
    if (new Date(tx.date) >= startDate) {
      if (tx.amount > 0) income += tx.amount
      else expenses += Math.abs(tx.amount)
    }
  }
  return { income, expenses: -expenses, net: income - expenses }
}

export function Dashboard() {
  const { transactions: storedTxns, recommendations: storedRecs, setTransactions, setRecommendations } = useAppStore()
  const [period, setPeriod] = useState<Period>('monthly')

  // Load real data from Rust backend on mount
  useEffect(() => {
    Promise.all([
      invoke<Transaction[]>('get_transactions').catch(() => null),
      invoke<Recommendation[]>('get_recommendations').catch(() => null),
    ]).then(([txns, recs]) => {
      if (txns && txns.length > 0) {
        setTransactions(txns)
      }
      if (recs && recs.length > 0) {
        setRecommendations(recs)
      }
    })
  }, [setRecommendations, setTransactions])

  const chartData = useMemo(
    () => (storedTxns.length > 0 ? buildSixMonthCashflowChart(storedTxns) : CASHFLOW_CHART_FALLBACK),
    [storedTxns],
  )

  // Use real data if available, fall back to mock for development
  const transactions = storedTxns.length > 0 ? storedTxns : MOCK_TRANSACTIONS
  const recommendations = storedRecs.length > 0 ? storedRecs : MOCK_RECOMMENDATIONS

  const cashflow = storedTxns.length > 0
    ? buildCashflowFromTransactions(storedTxns, period)
    : MOCK_CASHFLOW[period]

  const categorySpend = storedTxns.length > 0
    ? buildCategorySpend(storedTxns)
    : [
        { name: 'Groceries',     value: 287, color: '#12c97d' },
        { name: 'Dining',        value: 180, color: '#f59e0b' },
        { name: 'Transport',     value: 120, color: '#60a5fa' },
        { name: 'Utilities',     value: 189, color: '#94a3b8' },
        { name: 'Entertainment', value: 65,  color: '#a78bfa' },
        { name: 'Other',         value: 212, color: '#475569' },
      ]

  const anomalies = transactions.filter(t => t.isAnomaly)
  const pendingRecs = recommendations.filter(r => r.status === 'pending')

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {anomalies.length > 0 && (
        <div
          className="flex items-start gap-3 px-4 py-3 rounded-xl bg-amber-600/10 border border-amber-600/25 animate-fade-in"
          role="status"
        >
          <AlertCircle size={18} className="text-amber-400 flex-shrink-0 mt-0.5" aria-hidden />
          <p className="text-sm text-amber-200 leading-snug">
            <span className="font-semibold text-amber-100">
              {anomalies.length === 1 ? '1 anomaly' : `${anomalies.length} anomalies`} detected:{' '}
            </span>
            <span className="text-amber-200/95">
              {anomalies[0].merchantName} — {anomalies[0].anomalyReason}
            </span>
          </p>
        </div>
      )}

      <div className="grid grid-cols-12 gap-4">
        <NetWorthCard
          totalAUD={MOCK_NET_WORTH.totalAUD}
          changeAmount={2_340.50}
          changePct={2.75}
          changePeriod="30d"
          breakdown={[
            { label: 'Cash',        amountAUD: MOCK_NET_WORTH.cashAUD,        colorClass: 'bg-blue-400'    },
            { label: 'Investments', amountAUD: MOCK_NET_WORTH.investmentsAUD, colorClass: 'bg-emerald-500' },
            { label: 'Super',       amountAUD: MOCK_NET_WORTH.superAUD,       colorClass: 'bg-indigo-400'  },
            { label: 'Liabilities', amountAUD: MOCK_NET_WORTH.liabilitiesAUD, colorClass: 'bg-rose-500'    },
          ]}
        />

        <div className="col-span-12 lg:col-span-5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Cashflow</h2>
            <CashflowToggle period={period} onChange={setPeriod} />
          </div>
          <MetricCard title="Income"   value={cashflow.income}             format="currency" trend="up"   trendValue={3.2}  trendLabel="vs prev period" variant="positive" />
          <MetricCard title="Expenses" value={Math.abs(cashflow.expenses)} format="currency" trend="down" trendValue={-8.1} trendLabel="vs prev period" variant="negative" />
          <MetricCard title="Net"      value={cashflow.net}                format="currency" variant={cashflow.net > 0 ? 'positive' : 'negative'} />
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-8 rounded-lg bg-navy-800 border border-navy-600/40 shadow-sm shadow-card-inner p-5">
          <h3 className="text-sm font-semibold text-white mb-4">6-Month Cashflow</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="income-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#12c97d" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#12c97d" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="expense-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#e11d48" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#e11d48" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(38,58,115,0.3)" strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fill: '#4d6aa8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#4d6aa8', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip contentStyle={CUSTOM_TOOLTIP_STYLE} formatter={(v) => [formatAUD(v as number), '']} />
              <Area type="monotone" dataKey="income"   stroke="#12c97d" fill="url(#income-grad)"  strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="expenses" stroke="#e11d48" fill="url(#expense-grad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="col-span-12 lg:col-span-4 rounded-lg bg-navy-800 border border-navy-600/40 shadow-sm shadow-card-inner p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Spending by Category</h3>
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Pie data={categorySpend} cx="50%" cy="50%" innerRadius={45} outerRadius={65} paddingAngle={2} dataKey="value">
                {categorySpend.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-col gap-1.5 mt-2">
            {categorySpend.slice(0, 4).map(item => (
              <div key={item.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
                  <span className="text-xs text-navy-300">{item.name}</span>
                </div>
                <span className="text-xs font-mono tabular-nums text-navy-200">{formatAUD(item.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {pendingRecs.length > 0 && (
        <div className="rounded-lg bg-navy-800 border border-navy-600/40 shadow-sm shadow-card-inner p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Top Insights</h3>
          <div className="flex flex-col gap-2">
            {pendingRecs.slice(0, 3).map(rec => (
              <div key={rec.id} className="flex items-start gap-3 p-3 rounded-lg bg-navy-850/60 border border-navy-700/40 hover:border-navy-600/60 transition-colors duration-150">
                <InsightGlyph category={rec.category} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white leading-tight">{rec.title}</p>
                  <p className="text-xs text-navy-400 mt-0.5 line-clamp-1">{rec.body}</p>
                </div>
                <span className={cn(
                  'flex-shrink-0 px-2 py-0.5 rounded-full text-xs font-medium border capitalize',
                  rec.priority === 'high' ? 'bg-rose-600/15 text-rose-400 border-rose-600/25' :
                  rec.priority === 'medium' ? 'bg-amber-600/15 text-amber-400 border-amber-600/25' :
                  'bg-navy-700/50 text-navy-300 border-navy-600/40'
                )}>
                  {rec.priority}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
