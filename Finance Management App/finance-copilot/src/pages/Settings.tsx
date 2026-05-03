import { useState, useEffect } from 'react'
import { Eye, EyeOff, Shield, Cpu, Trash2, Link, AlertTriangle, Check, Sun, Moon } from 'lucide-react'
import { invoke } from '@tauri-apps/api/core'
import { useAppStore } from '../stores/appStore'
import { cn } from '../lib/cn'
import type { HardwareProfile, InferenceBackend, ModelTier } from '../types'

const INFERENCE_BACKENDS: InferenceBackend[] = ['cuda', 'vulkan', 'openvino', 'cpu']

function coerceHardwareProfile(raw: Record<string, unknown>): HardwareProfile {
  const b = String(raw.backend ?? 'cpu')
  const backend: InferenceBackend = INFERENCE_BACKENDS.includes(b as InferenceBackend)
    ? (b as InferenceBackend)
    : 'cpu'
  const tierRaw = String(raw.modelTier ?? raw.model_tier ?? '3B')
  const modelTier: ModelTier = tierRaw === '7B' ? '7B' : '3B'
  const gpuName = (raw.gpuName ?? raw.gpu_name) as string | undefined
  const vramGB = (raw.vramGB ?? raw.vram_gb) as number | undefined
  const ramGB = Number(raw.ramGB ?? raw.ram_gb ?? 0)
  return { backend, modelTier, gpuName, vramGB, ramGB, detectedAt: new Date() }
}

function Section({ title, icon: Icon, children }: {
  title: string
  icon: React.FC<{ size?: number; className?: string }>
  children: React.ReactNode
}) {
  return (
    <div className="rounded-lg bg-navy-800 border border-navy-600/40 shadow-sm shadow-card-inner p-6">
      <div className="flex items-center gap-2.5 mb-5">
        <Icon size={16} className="text-emerald-400" />
        <h2 className="text-sm font-semibold text-white">{title}</h2>
      </div>
      {children}
    </div>
  )
}

function LabeledInput({
  label, value, onChange, type = 'text', placeholder, hint,
}: {
  label: string; value: string; onChange: (v: string) => void
  type?: string; placeholder?: string; hint?: string
}) {
  const [show, setShow] = useState(false)
  const isPassword = type === 'password'

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium text-navy-300 uppercase tracking-wider">{label}</label>
      <div className="relative">
        <input
          type={isPassword && !show ? 'password' : 'text'}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full px-3 py-2.5 text-sm bg-navy-900 border border-navy-600/50 rounded-md text-white placeholder-navy-500 focus:outline-none focus:border-emerald-600/50 focus:ring-1 focus:ring-emerald-600/30 transition-colors pr-10"
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShow(v => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-navy-400 hover:text-navy-200 transition-colors"
          >
            {show ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        )}
      </div>
      {hint && <p className="text-xs text-navy-500">{hint}</p>}
    </div>
  )
}

export function Settings() {
  const { settings, updateSettings, hardwareProfile, setHardwareProfile, setTransactions, setRecommendations, theme, setTheme } = useAppStore()
  const [showWipeConfirm, setShowWipeConfirm] = useState(false)
  const [basiqKey, setBasiqKey] = useState(settings.basiqApiKey)
  const [eodhdKey, setEodhdKey] = useState(settings.eodhdApiKey)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [wipeStatus, setWipeStatus] = useState<'idle' | 'wiping' | 'done' | 'error'>('idle')

  useEffect(() => {
    invoke<{ basiqApiKey: string; eodhdApiKey: string }>('get_api_keys')
      .then(keys => {
        if (keys.basiqApiKey) setBasiqKey(keys.basiqApiKey)
        if (keys.eodhdApiKey) setEodhdKey(keys.eodhdApiKey)
      })
      .catch(() => {}) // keyring unavailable — silently ignore

    invoke<Record<string, unknown>>('detect_hardware')
      .then(hw => setHardwareProfile(coerceHardwareProfile(hw)))
      .catch(() => {})
  }, [setHardwareProfile])

  const handleSave = async () => {
    setSaveStatus('saving')
    try {
      await invoke('save_api_keys', { basiqKey, eodhdKey })
      updateSettings({ basiqApiKey: basiqKey, eodhdApiKey: eodhdKey })
      setSaveStatus('saved')
      setTimeout(() => setSaveStatus('idle'), 2000)
    } catch {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 3000)
    }
  }

  const handleWipe = async () => {
    setWipeStatus('wiping')
    try {
      await invoke('wipe_all_data')
      updateSettings({ basiqApiKey: '', eodhdApiKey: '', connectedAccounts: [] })
      setBasiqKey('')
      setEodhdKey('')
      setTransactions([])
      setRecommendations([])
      setWipeStatus('done')
      setTimeout(() => {
        setWipeStatus('idle')
        setShowWipeConfirm(false)
      }, 1500)
    } catch {
      setWipeStatus('error')
      setTimeout(() => setWipeStatus('idle'), 3000)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-6 max-w-2xl mx-auto space-y-6 pb-10">
      <Section title="Appearance" icon={Sun}>
        <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-4">
          Applies to the app chrome and backgrounds. Cards and charts keep strong contrast so numbers stay readable.
        </p>
        <div
          className="inline-flex rounded-lg border border-navy-600/40 p-1 bg-navy-900/80"
          role="group"
          aria-label="Color theme"
        >
          <button
            type="button"
            onClick={() => setTheme('dark')}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150',
              theme === 'dark'
                ? 'bg-navy-750 text-white shadow-sm'
                : 'text-navy-400 hover:text-navy-200',
            )}
            aria-pressed={theme === 'dark'}
          >
            <Moon size={15} className="opacity-80" aria-hidden />
            Dark
          </button>
          <button
            type="button"
            onClick={() => setTheme('light')}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150',
              theme === 'light'
                ? 'bg-navy-750 text-white shadow-sm'
                : 'text-navy-400 hover:text-navy-200',
            )}
            aria-pressed={theme === 'light'}
          >
            <Sun size={15} className="opacity-80" aria-hidden />
            Light
          </button>
        </div>
      </Section>

      <Section title="Bank Connection" icon={Link}>
        <div className="flex flex-col gap-4">
          <LabeledInput
            label="Basiq API Key"
            value={basiqKey}
            onChange={setBasiqKey}
            type="password"
            placeholder="sk_live_..."
            hint="Get your free API key at basiq.io — required for bank data sync"
          />
          <LabeledInput
            label="EODHD API Key"
            value={eodhdKey}
            onChange={setEodhdKey}
            type="password"
            placeholder="eodhd_..."
            hint="Optional — required for ASX market data. Free tier available at eodhd.com"
          />

          {settings.connectedAccounts.length > 0 && (
            <div className="mt-2">
              <p className="text-xs font-medium text-navy-300 uppercase tracking-wider mb-2">Connected Accounts</p>
              <div className="flex flex-col gap-2">
                {settings.connectedAccounts.map(acc => (
                  <div key={acc.id} className="flex items-center justify-between px-3 py-2 rounded-md bg-navy-850 border border-navy-700/40">
                    <div>
                      <p className="text-sm text-white font-medium">{acc.name}</p>
                      <p className="text-xs text-navy-400">{acc.institution} · {acc.type}</p>
                    </div>
                    <span className="text-sm font-mono tabular-nums text-emerald-400">
                      ${acc.balanceAUD.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={handleSave}
            disabled={saveStatus === 'saving'}
            className="mt-2 flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white text-sm font-medium transition-colors duration-150 active:scale-95 w-fit"
          >
            {saveStatus === 'saving' && <span className="animate-spin">⟳</span>}
            {saveStatus === 'saved' && <Check size={14} />}
            {saveStatus === 'saved' ? 'Saved to keychain' : saveStatus === 'error' ? 'Save failed' : 'Save API Keys'}
          </button>
        </div>
      </Section>

      <Section title="Hardware & Model" icon={Cpu}>
        {hardwareProfile ? (
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Inference backend', value: hardwareProfile.backend.toUpperCase() },
              { label: 'Model tier',        value: `Qwen ${hardwareProfile.modelTier}` },
              { label: 'RAM',               value: `${hardwareProfile.ramGB} GB` },
              { label: 'GPU',               value: hardwareProfile.gpuName ?? 'CPU only' },
            ].map(({ label, value }) => (
              <div key={label} className="flex flex-col gap-1 p-3 rounded-md bg-navy-850 border border-navy-700/40">
                <p className="text-xs text-navy-400">{label}</p>
                <p className="text-sm text-white font-medium font-mono">{value}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-4 py-3 rounded-md bg-amber-600/10 border border-amber-600/25">
            <p className="text-sm text-amber-300">Detecting hardware...</p>
          </div>
        )}
      </Section>

      <Section title="Security" icon={Shield}>
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-md bg-emerald-600/10 border border-emerald-600/20">
            <Shield size={14} className="text-emerald-400 flex-shrink-0" />
            <p className="text-xs text-emerald-300">API keys stored in OS credential vault · All data on-device only · No telemetry</p>
          </div>
        </div>
      </Section>

      <Section title="Data Management" icon={Trash2}>
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-md bg-rose-600/10 border border-rose-600/25">
            <AlertTriangle size={14} className="text-rose-400 flex-shrink-0" />
            <p className="text-xs text-rose-300">Wiping deletes all transactions, portfolio data, and chat history. This cannot be undone.</p>
          </div>

          {!showWipeConfirm ? (
            <button
              onClick={() => setShowWipeConfirm(true)}
              className="px-4 py-2 rounded-md bg-rose-600/15 hover:bg-rose-600/25 text-rose-400 text-sm font-medium border border-rose-600/30 hover:border-rose-500/40 transition-all duration-150 w-fit"
            >
              Wipe All Local Data
            </button>
          ) : (
            <div className="flex flex-col gap-2 p-4 rounded-md bg-rose-950/30 border border-rose-600/40">
              <p className="text-sm text-rose-200 font-medium">Are you absolutely sure?</p>
              <p className="text-xs text-rose-400">This will delete all transactions, holdings, recommendations, and chat history permanently.</p>
              <div className="flex gap-2 mt-1">
                <button
                  onClick={() => setShowWipeConfirm(false)}
                  disabled={wipeStatus === 'wiping'}
                  className="px-3 py-1.5 rounded-md text-sm bg-navy-700 text-navy-300 border border-navy-600/50 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleWipe}
                  disabled={wipeStatus === 'wiping' || wipeStatus === 'done'}
                  className="px-3 py-1.5 rounded-md text-sm bg-rose-600 hover:bg-rose-500 disabled:opacity-60 text-white font-medium transition-colors"
                >
                  {wipeStatus === 'wiping' ? 'Wiping...' : wipeStatus === 'done' ? 'Wiped' : 'Confirm Wipe'}
                </button>
              </div>
              {wipeStatus === 'error' && (
                <p className="text-xs text-rose-400">Wipe failed — check app logs.</p>
              )}
            </div>
          )}
        </div>
      </Section>
    </div>
  )
}
