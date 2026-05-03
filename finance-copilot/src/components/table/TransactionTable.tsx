import { useState } from 'react'
import { Search, Filter, ChevronUp, ChevronDown, AlertTriangle } from 'lucide-react'
import { cn } from '../../lib/cn'
import { formatAUD, formatDate } from '../../lib/formatters'
import { CATEGORY_COLORS, type Transaction, type TransactionCategory } from '../../types'
import { SkeletonRow } from '../common/SkeletonLoader'

interface TransactionTableProps {
  transactions: Transaction[]
  isLoading: boolean
}

function MerchantAvatar({ name, logoUrl }: { name: string; logoUrl?: string }) {
  if (logoUrl) {
    return (
      <img
        src={logoUrl}
        alt={name}
        className="w-7 h-7 rounded-md object-cover border border-navy-600/40"
      />
    )
  }
  return (
    <div className="w-7 h-7 rounded-md bg-navy-700 border border-navy-600/50 flex items-center justify-center text-xs text-navy-400 font-bold uppercase">
      {name.slice(0, 2)}
    </div>
  )
}

function CategoryPill({ category }: { category: TransactionCategory }) {
  const colors = CATEGORY_COLORS[category]
  return (
    <span className={cn(
      'inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium border',
      colors.bg, colors.text, colors.border
    )}>
      {colors.label}
    </span>
  )
}

type SortCol = 'date' | 'amount' | 'merchantName' | 'category'

function SortIcon({
  col,
  activeCol,
  sortDir,
}: {
  col: SortCol
  activeCol: SortCol
  sortDir: 'asc' | 'desc'
}) {
  if (activeCol !== col) return <ChevronDown size={12} className="opacity-30" />
  return sortDir === 'asc'
    ? <ChevronUp size={12} className="text-emerald-400" />
    : <ChevronDown size={12} className="text-emerald-400" />
}

function SortBtn({
  col,
  label,
  activeCol,
  sortDir,
  onSort,
}: {
  col: SortCol
  label: string
  activeCol: SortCol
  sortDir: 'asc' | 'desc'
  onSort: (col: SortCol) => void
}) {
  return (
    <button
      type="button"
      onClick={() => onSort(col)}
      className="flex items-center gap-1 text-xs font-semibold text-navy-300 uppercase tracking-wider hover:text-white transition-colors duration-100"
    >
      {label}
      <SortIcon col={col} activeCol={activeCol} sortDir={sortDir} />
    </button>
  )
}

export function TransactionTable({ transactions, isLoading }: TransactionTableProps) {
  const [search, setSearch] = useState('')
  const [filterCat, setFilterCat] = useState<TransactionCategory | 'all'>('all')
  const [sortCol, setSortCol] = useState<SortCol>('date')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const handleSort = (col: SortCol) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('desc') }
  }

  const filtered = transactions
    .filter(t => {
      if (filterCat !== 'all' && t.category !== filterCat) return false
      if (search) {
        const q = search.toLowerCase()
        return t.merchantName.toLowerCase().includes(q) ||
               t.description.toLowerCase().includes(q)
      }
      return true
    })
    .sort((a, b) => {
      let cmp = 0
      if (sortCol === 'date')         cmp = a.date.getTime() - b.date.getTime()
      else if (sortCol === 'amount')  cmp = a.amount - b.amount
      else if (sortCol === 'merchantName') cmp = a.merchantName.localeCompare(b.merchantName)
      else if (sortCol === 'category')    cmp = a.category.localeCompare(b.category)
      return sortDir === 'asc' ? cmp : -cmp
    })

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-3 p-4 border-b border-navy-600/40 flex-shrink-0">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-navy-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search transactions..."
            className="w-full pl-8 pr-3 py-2 text-sm bg-navy-800 border border-navy-600/50 rounded-md text-white placeholder-navy-400 focus:outline-none focus:border-emerald-600/50 focus:ring-1 focus:ring-emerald-600/30 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter size={14} className="text-navy-400" />
          <select
            value={filterCat}
            onChange={e => setFilterCat(e.target.value as TransactionCategory | 'all')}
            className="text-sm bg-navy-800 border border-navy-600/50 rounded-md text-navy-200 px-2.5 py-2 focus:outline-none focus:border-emerald-600/50 transition-colors"
          >
            <option value="all">All categories</option>
            {Object.entries(CATEGORY_COLORS).map(([k, v]) => (
              <option key={k} value={k}>{v.label}</option>
            ))}
          </select>
        </div>

        {selected.size > 0 && (
          <span className="text-xs text-navy-300">
            {selected.size} selected
          </span>
        )}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10">
            <tr className="bg-navy-700 border-b border-navy-600/60">
              <th className="w-10 px-4 py-3">
                <input
                  type="checkbox"
                  checked={selected.size === filtered.length && filtered.length > 0}
                  onChange={() => {
                    if (selected.size === filtered.length) setSelected(new Set())
                    else setSelected(new Set(filtered.map(t => t.id)))
                  }}
                  className="accent-emerald-500"
                />
              </th>
              <th className="px-4 py-3 text-left"><SortBtn col="date" label="Date" activeCol={sortCol} sortDir={sortDir} onSort={handleSort} /></th>
              <th className="px-4 py-3 text-left"><SortBtn col="merchantName" label="Merchant" activeCol={sortCol} sortDir={sortDir} onSort={handleSort} /></th>
              <th className="px-4 py-3 text-left"><SortBtn col="category" label="Category" activeCol={sortCol} sortDir={sortDir} onSort={handleSort} /></th>
              <th className="px-4 py-3 text-right"><SortBtn col="amount" label="Amount" activeCol={sortCol} sortDir={sortDir} onSort={handleSort} /></th>
              <th className="px-4 py-3 text-right">
                <span className="text-xs font-semibold text-navy-300 uppercase tracking-wider">Balance</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading
              ? Array.from({ length: 8 }).map((_, i) => <tr key={i}><td colSpan={6}><SkeletonRow /></td></tr>)
              : filtered.length === 0
              ? (
                <tr>
                  <td colSpan={6} className="px-4 py-16 text-center text-navy-400 text-sm">
                    No transactions found
                  </td>
                </tr>
              )
              : filtered.map(t => (
                <tr
                  key={t.id}
                  className={cn(
                    'border-b border-navy-700/50 transition-colors duration-100 group',
                    selected.has(t.id) ? 'bg-navy-750/50 border-l-2 border-l-emerald-500' : 'hover:bg-navy-800/60',
                    t.isAnomaly && !selected.has(t.id) && 'border-l-2 border-l-amber-500',
                  )}
                >
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selected.has(t.id)}
                      onChange={() => toggleSelect(t.id)}
                      className="accent-emerald-500"
                    />
                  </td>
                  <td className="px-4 py-3 text-sm text-navy-300 whitespace-nowrap">
                    {formatDate(t.date)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <MerchantAvatar name={t.merchantName} logoUrl={t.merchantLogoUrl} />
                      <div>
                        <p className="text-sm text-white font-medium leading-tight">{t.merchantName}</p>
                        <p className="text-xs text-navy-400 truncate max-w-[200px]">{t.description}</p>
                      </div>
                      {t.isAnomaly && (
                        <span title={t.anomalyReason}><AlertTriangle size={13} className="text-amber-400 flex-shrink-0" /></span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <CategoryPill category={t.category} />
                  </td>
                  <td className={cn(
                    'px-4 py-3 text-sm font-mono tabular-nums whitespace-nowrap text-right font-medium',
                    t.amount >= 0 ? 'text-emerald-400' : 'text-white'
                  )}>
                    {formatAUD(t.amount, { signed: t.amount > 0 })}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono tabular-nums text-navy-300 whitespace-nowrap text-right">
                    {formatAUD(t.runningBalance)}
                  </td>
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-navy-600/40 flex-shrink-0">
        <span className="text-xs text-navy-400">
          {filtered.length} transactions
        </span>
      </div>
    </div>
  )
}
