import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  Transaction, Holding, ChatMessage, Recommendation,
  AppSettings, NetWorthSnapshot, SyncStatus, HardwareProfile,
} from '../types'

interface AppState {
  // App state
  sidebarCollapsed: boolean
  theme: 'dark' | 'light'
  onboardingComplete: boolean
  syncStatus: SyncStatus
  lastSyncTime?: Date
  hardwareProfile?: HardwareProfile

  // Data
  transactions: Transaction[]
  holdings: Holding[]
  messages: ChatMessage[]
  recommendations: Recommendation[]
  netWorthHistory: NetWorthSnapshot[]

  // Settings
  settings: AppSettings

  // Actions
  setSidebarCollapsed: (collapsed: boolean) => void
  toggleSidebar: () => void
  setTheme: (theme: 'dark' | 'light') => void
  setOnboardingComplete: (v: boolean) => void
  setSyncStatus: (status: SyncStatus) => void
  setLastSyncTime: (date: Date) => void
  setHardwareProfile: (profile: HardwareProfile) => void
  setTransactions: (txns: Transaction[]) => void
  setHoldings: (holdings: Holding[]) => void
  addMessage: (msg: ChatMessage) => void
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void
  clearMessages: () => void
  setRecommendations: (recs: Recommendation[]) => void
  acceptRecommendation: (id: string) => void
  snoozeRecommendation: (id: string, until: Date) => void
  dismissRecommendation: (id: string) => void
  updateSettings: (updates: Partial<AppSettings>) => void
}

const DEFAULT_SETTINGS: AppSettings = {
  basiqApiKey: '',
  eodhdApiKey: '',
  connectedAccounts: [],
  theme: 'dark',
  sidebarCollapsed: false,
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      theme: 'dark',
      onboardingComplete: false,
      syncStatus: 'never',
      transactions: [],
      holdings: [],
      messages: [],
      recommendations: [],
      netWorthHistory: [],
      settings: DEFAULT_SETTINGS,

      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setTheme: (theme) => set((s) => ({
        theme,
        settings: { ...s.settings, theme },
      })),
      setOnboardingComplete: (v) => set({ onboardingComplete: v }),
      setSyncStatus: (syncStatus) => set({ syncStatus }),
      setLastSyncTime: (date) => set({ lastSyncTime: date }),
      setHardwareProfile: (hardwareProfile) => set({ hardwareProfile }),
      setTransactions: (transactions) => set({ transactions }),
      setHoldings: (holdings) => set({ holdings }),
      addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
      updateMessage: (id, updates) => set((s) => ({
        messages: s.messages.map((m) => m.id === id ? { ...m, ...updates } : m),
      })),
      clearMessages: () => set({ messages: [] }),
      setRecommendations: (recommendations) => set({ recommendations }),
      acceptRecommendation: (id) => set((s) => ({
        recommendations: s.recommendations.map((r) =>
          r.id === id ? { ...r, status: 'accepted' as const } : r
        ),
      })),
      snoozeRecommendation: (id, snoozeUntil) => set((s) => ({
        recommendations: s.recommendations.map((r) =>
          r.id === id ? { ...r, status: 'snoozed' as const, snoozeUntil } : r
        ),
      })),
      dismissRecommendation: (id) => set((s) => ({
        recommendations: s.recommendations.map((r) =>
          r.id === id ? { ...r, status: 'dismissed' as const } : r
        ),
      })),
      updateSettings: (updates) => set((s) => ({ settings: { ...s.settings, ...updates } })),
    }),
    {
      name: 'finance-copilot',
      partialize: (s) => ({
        theme: s.theme,
        onboardingComplete: s.onboardingComplete,
        sidebarCollapsed: s.sidebarCollapsed,
        settings: s.settings,
        hardwareProfile: s.hardwareProfile,
      }),
    }
  )
)
