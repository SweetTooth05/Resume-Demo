import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { cn } from '../../lib/cn'

interface SuggestedPrompt {
  label: string
  prompt: string
}

const SUGGESTED_PROMPTS: SuggestedPrompt[] = [
  { label: 'Can I afford a $3k holiday?',  prompt: 'Can I afford a $3,000 holiday in October based on my current cashflow?' },
  { label: 'Top 3 spending categories',    prompt: 'What are my top 3 spending categories this month?' },
  { label: 'Portfolio performance YTD',    prompt: 'How is my portfolio performing year-to-date?' },
  { label: 'Savings rate this year',       prompt: 'What has my average savings rate been this year?' },
]

interface ChatInputProps {
  onSend: (message: string) => void
  isStreaming: boolean
  disabled?: boolean
}

export function ChatInput({ onSend, isStreaming, disabled }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`
    }
  }, [value])

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || isStreaming || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col gap-3 p-4 border-t border-[var(--surface-border)] bg-[color-mix(in_srgb,var(--surface-raised)_75%,transparent)] backdrop-blur-md">
      {/* Suggested prompts */}
      <div className="flex items-center gap-2 flex-wrap">
        {SUGGESTED_PROMPTS.map((sp) => (
          <button
            key={sp.label}
            onClick={() => { setValue(sp.prompt); textareaRef.current?.focus() }}
            className="px-3 py-1 rounded-full text-xs text-navy-300 bg-navy-800 border border-navy-600/40 hover:text-white hover:border-navy-500/60 hover:bg-navy-750 transition-all duration-150"
          >
            {sp.label}
          </button>
        ))}
      </div>

      {/* Input row */}
      <div className="flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask anything about your finances..."
            rows={1}
            disabled={disabled}
            className={cn(
              'w-full px-4 py-3 pr-12 text-sm bg-navy-800 border border-navy-600/50 rounded-xl',
              'text-white placeholder-navy-400 resize-none overflow-hidden',
              'focus:outline-none focus:border-emerald-600/50 focus:ring-1 focus:ring-emerald-600/30',
              'transition-colors duration-150 leading-relaxed',
              'disabled:opacity-50 disabled:cursor-not-allowed',
            )}
          />
        </div>

        <button
          onClick={handleSend}
          disabled={!value.trim() || isStreaming || disabled}
          className={cn(
            'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center',
            'transition-all duration-150 active:scale-95',
            value.trim() && !isStreaming && !disabled
              ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-glow'
              : 'bg-navy-700 text-navy-500 cursor-not-allowed',
          )}
        >
          {isStreaming
            ? <Loader2 size={16} className="animate-spin" />
            : <Send size={16} />
          }
        </button>
      </div>
    </div>
  )
}
