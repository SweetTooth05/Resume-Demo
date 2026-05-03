import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight, ChevronLeft, Check, LineChart } from 'lucide-react'
import { cn } from '../lib/cn'
import { useAppStore } from '../stores/appStore'

interface Step {
  id: number
  title: string
  subtitle: string
  field: string
  type: 'choice' | 'scale' | 'text' | 'info'
  options?: string[]
}

const STEPS: Step[] = [
  { id: 1, title: 'Financial priorities', subtitle: 'What matters most to you right now?', field: 'priority', type: 'choice', options: ['Save for a goal', 'Reduce debt', 'Grow investments', 'Understand my spending', 'Plan for retirement'] },
  { id: 2, title: 'Risk tolerance', subtitle: 'How do you feel about investment risk?', field: 'riskTolerance', type: 'choice', options: ['Conservative — protect capital', 'Balanced — moderate growth', 'Growth — accept volatility', 'Aggressive — maximise returns'] },
  { id: 3, title: 'Retirement horizon', subtitle: 'When do you plan to retire?', field: 'retirementHorizon', type: 'choice', options: ['< 5 years', '5–10 years', '10–20 years', '20–30 years', '30+ years'] },
  { id: 4, title: 'Dependents', subtitle: 'Do you have financial dependents?', field: 'dependents', type: 'choice', options: ['None', '1 child', '2+ children', 'Partner (non-earning)', 'Elderly parent'] },
  { id: 5, title: 'Debt position', subtitle: 'What significant debts do you carry?', field: 'debt', type: 'choice', options: ['None', 'Mortgage only', 'HECS/student debt', 'Credit card debt', 'Personal loan', 'Multiple of the above'] },
  { id: 6, title: 'Savings goal', subtitle: 'What is your primary short-term savings goal?', field: 'savingsGoal', type: 'text' },
  { id: 7, title: 'Basiq API key', subtitle: 'Paste your Basiq API key to connect your bank accounts. All data stays on your device.', field: 'basiqKey', type: 'text' },
  { id: 8, title: 'Ready to sync', subtitle: 'We\'ll pull your last 24 months of transactions and set up your local AI assistant.', field: 'sync', type: 'info' },
]

export function Onboarding() {
  const navigate = useNavigate()
  const { setOnboardingComplete, updateSettings } = useAppStore()
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [syncing, setSyncing] = useState(false)
  const [syncProgress, setSyncProgress] = useState(0)

  const current = STEPS[step]
  const isLast = step === STEPS.length - 1

  const handleChoice = (value: string) => {
    setAnswers(a => ({ ...a, [current.field]: value }))
  }

  const handleNext = async () => {
    if (isLast) {
      setSyncing(true)
      // Simulate sync progress
      for (let i = 0; i <= 100; i += 5) {
        await new Promise(r => setTimeout(r, 80))
        setSyncProgress(i)
      }
      if (answers.basiqKey) {
        updateSettings({ basiqApiKey: answers.basiqKey })
      }
      setOnboardingComplete(true)
      navigate('/dashboard')
    } else {
      setStep(s => s + 1)
    }
  }

  const handleBack = () => setStep(s => Math.max(0, s - 1))

  const canAdvance = current.type === 'info' || !!answers[current.field]

  return (
    <div className="min-h-screen min-h-[100dvh] bg-[var(--surface-base)] flex items-center justify-center p-6">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-emerald-600/20 border border-emerald-600/30 flex items-center justify-center">
            <LineChart size={20} className="text-emerald-400" />
          </div>
          <span className="text-xl font-semibold text-[var(--text-primary)] tracking-tight">Finance Copilot</span>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-1 mb-8">
          {STEPS.map((s, i) => (
            <div
              key={s.id}
              className={cn(
                'flex-1 h-1 rounded-full transition-all duration-300',
                i < step ? 'bg-emerald-500' :
                i === step ? 'bg-emerald-600/60' :
                'bg-navy-700'
              )}
            />
          ))}
        </div>

        {/* Card */}
        <div className="rounded-2xl bg-navy-800 border border-navy-600/40 shadow-lg shadow-card-inner p-8 animate-fade-in">
          <div className="mb-2">
            <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">
              Step {step + 1} of {STEPS.length}
            </span>
          </div>
          <h1 className="text-xl font-semibold text-white mb-2">{current.title}</h1>
          <p className="text-sm text-navy-300 mb-6 leading-relaxed">{current.subtitle}</p>

          {/* Content */}
          {current.type === 'choice' && current.options && (
            <div className="flex flex-col gap-2">
              {current.options.map(opt => (
                <button
                  key={opt}
                  onClick={() => handleChoice(opt)}
                  className={cn(
                    'flex items-center justify-between px-4 py-3 rounded-lg border text-sm font-medium transition-all duration-150 text-left',
                    answers[current.field] === opt
                      ? 'bg-emerald-600/20 border-emerald-600/50 text-emerald-300'
                      : 'bg-navy-850 border-navy-700/60 text-navy-200 hover:border-navy-500/60 hover:text-white'
                  )}
                >
                  {opt}
                  {answers[current.field] === opt && (
                    <Check size={14} className="text-emerald-400 flex-shrink-0" />
                  )}
                </button>
              ))}
            </div>
          )}

          {current.type === 'text' && (
            <input
              type={current.field === 'basiqKey' ? 'password' : 'text'}
              value={answers[current.field] ?? ''}
              onChange={e => handleChoice(e.target.value)}
              placeholder={current.field === 'basiqKey' ? 'sk_live_...' : 'e.g. Save $20,000 for a house deposit'}
              className="w-full px-4 py-3 text-sm bg-navy-900 border border-navy-600/50 rounded-lg text-white placeholder-navy-500 focus:outline-none focus:border-emerald-600/50 focus:ring-1 focus:ring-emerald-600/30 transition-colors"
            />
          )}

          {current.type === 'info' && !syncing && (
            <div className="flex flex-col gap-3">
              {['Pull 24 months of transaction history', 'Run hardware detection probe', 'Load Qwen model weights', 'Generate your first insights'].map(item => (
                <div key={item} className="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-navy-850 border border-navy-700/40">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                  <span className="text-sm text-navy-200">{item}</span>
                </div>
              ))}
            </div>
          )}

          {syncing && (
            <div className="flex flex-col gap-4">
              <div className="h-2 rounded-full bg-navy-700 overflow-hidden">
                <div
                  className="h-2 rounded-full bg-emerald-500 transition-all duration-100"
                  style={{ width: `${syncProgress}%` }}
                />
              </div>
              <p className="text-sm text-center text-navy-300 tabular-nums">
                {syncProgress < 30 ? 'Connecting to Basiq...' :
                 syncProgress < 60 ? 'Pulling transactions...' :
                 syncProgress < 85 ? 'Running hardware probe...' :
                 'Loading model weights...'}
              </p>
            </div>
          )}
        </div>

        {/* Navigation */}
        {!syncing && (
          <div className="flex items-center justify-between mt-6">
            <button
              onClick={handleBack}
              disabled={step === 0}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-navy-400 hover:text-navy-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={16} />
              Back
            </button>

            <button
              onClick={handleNext}
              disabled={!canAdvance}
              className={cn(
                'flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 active:scale-95',
                canAdvance
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                  : 'bg-navy-700 text-navy-500 cursor-not-allowed'
              )}
            >
              {isLast ? 'Start Sync' : 'Continue'}
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
