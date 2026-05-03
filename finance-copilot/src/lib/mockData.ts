import type { Transaction, Holding, Recommendation, NetWorthSnapshot } from '../types'

export const MOCK_TRANSACTIONS: Transaction[] = [
  { id: '1', date: new Date('2026-04-22'), merchantName: 'Woolworths', description: 'Woolworths Bondi', amount: -134.50, runningBalance: 12450.20, category: 'groceries', accountId: 'acc1', accountName: 'Everyday Account', tags: [], isAnomaly: true, anomalyReason: '22% above 90-day average' },
  { id: '2', date: new Date('2026-04-22'), merchantName: 'Sydney Trains', description: 'Opal card top-up', amount: -50.00, runningBalance: 12584.70, category: 'transport', accountId: 'acc1', accountName: 'Everyday Account', tags: [] },
  { id: '3', date: new Date('2026-04-21'), merchantName: 'Employer Pty Ltd', description: 'Salary — April 2026', amount: 5833.33, runningBalance: 12634.70, category: 'income', accountId: 'acc1', accountName: 'Everyday Account', tags: [] },
  { id: '4', date: new Date('2026-04-20'), merchantName: 'Netflix', description: 'Netflix subscription', amount: -22.99, runningBalance: 6801.37, category: 'entertainment', accountId: 'acc1', accountName: 'Everyday Account', tags: [] },
  { id: '5', date: new Date('2026-04-19'), merchantName: 'Priceline', description: 'Health & beauty', amount: -67.40, runningBalance: 6824.36, category: 'healthcare', accountId: 'acc1', accountName: 'Everyday Account', tags: [] },
  { id: '6', date: new Date('2026-04-18'), merchantName: 'Uber Eats', description: 'Food delivery', amount: -43.80, runningBalance: 6891.76, category: 'dining', accountId: 'acc1', accountName: 'Everyday Account', tags: [] },
  { id: '7', date: new Date('2026-04-17'), merchantName: 'AGL Energy', description: 'Electricity bill', amount: -189.00, runningBalance: 6935.56, category: 'utilities', accountId: 'acc1', accountName: 'Everyday Account', tags: [] },
  { id: '8', date: new Date('2026-04-16'), merchantName: 'Coles', description: 'Grocery shop', amount: -98.30, runningBalance: 7124.56, category: 'groceries', accountId: 'acc1', accountName: 'Everyday Account', tags: [] },
  { id: '9', date: new Date('2026-04-15'), merchantName: 'Stake', description: 'ASX investment', amount: -1000.00, runningBalance: 7222.86, category: 'investment', accountId: 'acc1', accountName: 'Everyday Account', tags: [] },
  { id: '10', date: new Date('2026-04-14'), merchantName: 'ALDI', description: 'Grocery shop', amount: -54.20, runningBalance: 8222.86, category: 'groceries', accountId: 'acc1', accountName: 'Everyday Account', tags: [] },
]

export const MOCK_HOLDINGS: Holding[] = [
  { ticker: 'VAS', name: 'Vanguard Australian Shares', units: 120, avgCostBasis: 98.50, currentPrice: 112.40, previousClose: 111.80, marketValueAUD: 13488, unrealisedPnL: 1668, unrealisedPnLPct: 14.11, allocationPct: 38.2, priceHistory: [] },
  { ticker: 'VGS', name: 'Vanguard Intl Shares', units: 85, avgCostBasis: 115.20, currentPrice: 138.60, previousClose: 137.90, marketValueAUD: 11781, unrealisedPnL: 1989, unrealisedPnLPct: 20.31, allocationPct: 33.4, priceHistory: [] },
  { ticker: 'BHP', name: 'BHP Group', units: 40, avgCostBasis: 44.20, currentPrice: 48.75, previousClose: 48.20, marketValueAUD: 1950, unrealisedPnL: 182, unrealisedPnLPct: 10.29, allocationPct: 5.5, priceHistory: [] },
  { ticker: 'CBA', name: 'Commonwealth Bank', units: 15, avgCostBasis: 120.50, currentPrice: 148.30, previousClose: 147.60, marketValueAUD: 2224.50, unrealisedPnL: 417, unrealisedPnLPct: 23.07, allocationPct: 6.3, priceHistory: [] },
  { ticker: 'NDQ', name: 'BetaShares NASDAQ 100', units: 50, avgCostBasis: 37.80, currentPrice: 48.20, previousClose: 47.95, marketValueAUD: 2410, unrealisedPnL: 520, unrealisedPnLPct: 27.51, allocationPct: 6.8, priceHistory: [] },
]

export const MOCK_RECOMMENDATIONS: Recommendation[] = [
  {
    id: 'r1',
    title: 'Reduce grocery spend to historical average',
    body: 'Your grocery spending is tracking 22% above your 90-day average this month. If you reduce to your average of $320/month, you\'d save approximately $384 over the next 6 months.',
    confidence: 0.87,
    category: 'spending',
    priority: 'high',
    status: 'pending',
    generatedAt: new Date('2026-04-23'),
    mcpCalls: [
      { toolName: 'query_transactions', args: { category: 'groceries', days: 90 }, result: { total: 960, avg_monthly: 320 }, durationMs: 34 },
      { toolName: 'compare_periods', args: { current: '2026-04', previous_avg: '90d' }, result: { delta_pct: 22.1 }, durationMs: 12 },
    ],
  },
  {
    id: 'r2',
    title: 'Increase VAS allocation for diversification',
    body: 'Your portfolio is overweight in international shares (VGS at 33%). Consider rebalancing by redirecting your next $1,000 investment to VAS to bring your AU/Intl ratio closer to 60/40.',
    confidence: 0.74,
    category: 'portfolio',
    priority: 'medium',
    status: 'pending',
    generatedAt: new Date('2026-04-23'),
    mcpCalls: [
      { toolName: 'query_transactions', args: { category: 'investment', days: 30 }, result: { total: 1000 }, durationMs: 28 },
    ],
  },
  {
    id: 'r3',
    title: 'Build 3-month emergency fund',
    body: 'Based on your monthly expenses of ~$3,800, a 3-month emergency fund would be $11,400. Your current savings account holds $6,200 — you\'re 54% of the way there.',
    confidence: 0.91,
    category: 'savings',
    priority: 'high',
    status: 'pending',
    generatedAt: new Date('2026-04-22'),
    mcpCalls: [
      { toolName: 'aggregate', args: { category: 'all', type: 'expenses', period: '30d' }, result: { total: 3812 }, durationMs: 45 },
      { toolName: 'calculate', args: { expr: '3812 * 3' }, result: 11436, durationMs: 2 },
    ],
  },
]

export const MOCK_NET_WORTH: NetWorthSnapshot = {
  totalAUD: 87_420.50,
  cashAUD: 18_650.30,
  investmentsAUD: 52_730.00,
  superAUD: 31_200.00,
  liabilitiesAUD: -15_160.00,
  date: new Date(),
}

export const MOCK_CASHFLOW = {
  weekly:  { income: 1458.33, expenses: -952.40, net: 505.93 },
  monthly: { income: 5833.33, expenses: -3812.60, net: 2020.73 },
  yearly:  { income: 70_000,  expenses: -45_751.20, net: 24_248.80 },
}
