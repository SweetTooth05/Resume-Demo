import { useState } from 'react'
import { Bot, ChevronDown, ChevronRight, Wrench } from 'lucide-react'
import { formatRelativeTime } from '../../lib/formatters'
import type { ChatMessage, McpToolCall } from '../../types'

function ToolCallPanel({ calls }: { calls: McpToolCall[] }) {
  return (
    <div className="mt-2 rounded-lg border border-navy-700/60 bg-navy-900/80 overflow-hidden animate-fade-in">
      <div className="px-3 py-2 bg-navy-850 border-b border-navy-700/60">
        <span className="text-xs font-medium text-navy-400 uppercase tracking-wider">
          Tool calls — {calls.length}
        </span>
      </div>
      {calls.map((call, i) => (
        <div key={i} className="px-3 py-2.5 border-b border-navy-700/40 last:border-b-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-mono text-amber-400 font-medium">{call.toolName}</span>
            <span className="text-2xs text-navy-500 tabular-nums">{call.durationMs}ms</span>
          </div>
          <pre className="text-xs font-mono text-navy-300 bg-navy-950/60 rounded px-2 py-1.5 overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify({ args: call.args, result: call.result }, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  )
}

interface ChatBubbleProps {
  message: ChatMessage
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const [workingExpanded, setWorkingExpanded] = useState(false)

  if (message.role === 'user') {
    return (
      <div className="flex justify-end mb-4 animate-fade-in">
        <div className="flex flex-col items-end gap-1 max-w-[65%]">
          <div className="px-4 py-3 rounded-xl rounded-tr-sm bg-navy-700 border border-navy-600/50 text-sm text-white leading-relaxed">
            {message.content}
          </div>
          <span className="text-2xs text-navy-500">{formatRelativeTime(message.timestamp)}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start mb-4 gap-2.5 animate-fade-in">
      {/* Avatar */}
      <div className="w-7 h-7 rounded-md bg-emerald-600/20 border border-emerald-600/30 flex items-center justify-center flex-shrink-0 mt-1">
        <Bot size={13} className="text-emerald-400" />
      </div>

      <div className="flex flex-col gap-1 max-w-[75%] min-w-0">
        <div className="px-4 py-3 rounded-xl rounded-tl-sm bg-navy-800 border border-navy-600/40 shadow-card-inner text-sm text-navy-100 leading-relaxed">
          {message.isStreaming ? (
            <>
              {message.content}
              <span className="inline-block w-0.5 h-4 bg-emerald-400 ml-0.5 animate-pulse" />
            </>
          ) : (
            message.content
          )}
        </div>

        {/* Show working toggle */}
        {message.mcpCalls && message.mcpCalls.length > 0 && (
          <button
            onClick={() => setWorkingExpanded(v => !v)}
            className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs text-navy-400 hover:text-navy-200 hover:bg-navy-800/50 transition-colors duration-150 w-fit"
          >
            <Wrench size={11} />
            <span>Show working</span>
            {workingExpanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
          </button>
        )}

        {workingExpanded && message.mcpCalls && (
          <ToolCallPanel calls={message.mcpCalls} />
        )}

        <span className="text-2xs text-navy-500">{formatRelativeTime(message.timestamp)}</span>
      </div>
    </div>
  )
}
