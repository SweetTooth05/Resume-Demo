export type NavRoute =
  | '/dashboard'
  | '/chat'
  | '/transactions'
  | '/portfolio'
  | '/recommendations'
  | '/settings'
  | '/onboarding'

export type TransactionCategory =
  | 'groceries'
  | 'dining'
  | 'transport'
  | 'utilities'
  | 'entertainment'
  | 'healthcare'
  | 'shopping'
  | 'income'
  | 'transfer'
  | 'investment'
  | 'insurance'
  | 'education'
  | 'travel'
  | 'other'

export interface Transaction {
  id: string
  date: Date
  merchantName: string
  merchantLogoUrl?: string
  description: string
  amount: number
  runningBalance: number
  category: TransactionCategory
  subcategory?: string
  accountId: string
  accountName: string
  tags: string[]
  isAnomaly?: boolean
  anomalyReason?: string
}

export interface Account {
  id: string
  name: string
  institution: string
  type: 'checking' | 'savings' | 'credit' | 'investment' | 'super'
  balanceAUD: number
  lastSynced: Date
}

export interface Holding {
  ticker: string
  name: string
  units: number
  avgCostBasis: number
  currentPrice: number
  previousClose: number
  marketValueAUD: number
  unrealisedPnL: number
  unrealisedPnLPct: number
  allocationPct: number
  priceHistory: { date: string; close: number }[]
}

export interface McpToolCall {
  toolName: string
  args: Record<string, unknown>
  result: unknown
  durationMs: number
}

export type MessageRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: Date
  mcpCalls?: McpToolCall[]
  isStreaming?: boolean
}

export type RecommendationCategory = 'savings' | 'spending' | 'portfolio' | 'tax' | 'cashflow'
export type RecommendationPriority = 'high' | 'medium' | 'low'
export type RecommendationStatus = 'pending' | 'accepted' | 'snoozed' | 'dismissed'

export interface Recommendation {
  id: string
  title: string
  body: string
  confidence: number
  category: RecommendationCategory
  priority: RecommendationPriority
  status: RecommendationStatus
  generatedAt: Date
  mcpCalls: McpToolCall[]
  snoozeUntil?: Date
}

export type SyncStatus = 'idle' | 'syncing' | 'error' | 'never'
export type ModelTier = '3B' | '7B'
export type InferenceBackend = 'cuda' | 'vulkan' | 'openvino' | 'cpu'

export interface HardwareProfile {
  backend: InferenceBackend
  modelTier: ModelTier
  gpuName?: string
  vramGB?: number
  ramGB: number
  detectedAt: Date
}

export interface AppSettings {
  basiqApiKey: string
  eodhdApiKey: string
  connectedAccounts: Account[]
  hardwareProfile?: HardwareProfile
  theme: 'dark' | 'light'
  sidebarCollapsed: boolean
}

export interface NetWorthSnapshot {
  totalAUD: number
  cashAUD: number
  investmentsAUD: number
  superAUD: number
  liabilitiesAUD: number
  date: Date
}

export const CATEGORY_COLORS: Record<TransactionCategory, {
  bg: string; text: string; border: string; label: string
}> = {
  groceries:     { bg: 'bg-emerald-600/15', text: 'text-emerald-400', border: 'border-emerald-600/25',  label: 'Groceries'    },
  dining:        { bg: 'bg-amber-600/15',   text: 'text-amber-400',   border: 'border-amber-600/25',    label: 'Dining'       },
  transport:     { bg: 'bg-blue-600/15',    text: 'text-blue-400',    border: 'border-blue-600/25',     label: 'Transport'    },
  utilities:     { bg: 'bg-slate-600/15',   text: 'text-slate-400',   border: 'border-slate-600/25',    label: 'Utilities'    },
  entertainment: { bg: 'bg-purple-600/15',  text: 'text-purple-400',  border: 'border-purple-600/25',   label: 'Entertainment'},
  healthcare:    { bg: 'bg-teal-600/15',    text: 'text-teal-400',    border: 'border-teal-600/25',     label: 'Healthcare'   },
  shopping:      { bg: 'bg-pink-600/15',    text: 'text-pink-400',    border: 'border-pink-600/25',     label: 'Shopping'     },
  income:        { bg: 'bg-emerald-600/20', text: 'text-emerald-300', border: 'border-emerald-500/30',  label: 'Income'       },
  transfer:      { bg: 'bg-navy-600/30',    text: 'text-navy-300',    border: 'border-navy-500/40',     label: 'Transfer'     },
  investment:    { bg: 'bg-indigo-600/15',  text: 'text-indigo-400',  border: 'border-indigo-600/25',   label: 'Investment'   },
  insurance:     { bg: 'bg-cyan-600/15',    text: 'text-cyan-400',    border: 'border-cyan-600/25',     label: 'Insurance'    },
  education:     { bg: 'bg-violet-600/15',  text: 'text-violet-400',  border: 'border-violet-600/25',   label: 'Education'    },
  travel:        { bg: 'bg-sky-600/15',     text: 'text-sky-400',     border: 'border-sky-600/25',      label: 'Travel'       },
  other:         { bg: 'bg-slate-700/30',   text: 'text-slate-400',   border: 'border-slate-600/30',    label: 'Other'        },
}
