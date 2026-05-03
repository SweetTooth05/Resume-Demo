import { useRef, useEffect, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { ChatBubble } from '../components/chat/ChatBubble'
import { ChatInput } from '../components/chat/ChatInput'
import { useAppStore } from '../stores/appStore'
import type { ChatMessage } from '../types'

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content: 'Your local finance assistant is ready. All data stays on this device. Ask me anything about your money.',
  timestamp: new Date(),
}

export function Chat() {
  const { messages, addMessage, updateMessage } = useAppStore()
  const isStreaming = messages.some(m => m.isStreaming)
  const scrollRef = useRef<HTMLDivElement>(null)
  const cleanupRef = useRef<Array<() => void>>([])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  useEffect(() => {
    return () => {
      const fns = [...cleanupRef.current]
      cleanupRef.current = []
      fns.forEach(fn => fn())
    }
  }, [])

  const handleSend = useCallback(async (text: string) => {
    const userMsg: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    addMessage(userMsg)

    const assistantId = uuidv4()
    addMessage({
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      mcpCalls: [],
    })

    // Build history for context window (last 10 exchanges)
    const history = messages.slice(-20).map(m => ({
      role: m.role,
      content: m.content,
    }))

    // Wire up token streaming events
    let accumulated = ''

    const unlistenToken = await listen<{ message_id: string; token: string }>(
      'chat-token',
      (event) => {
        if (event.payload.message_id !== assistantId) return
        accumulated += event.payload.token
        updateMessage(assistantId, { content: accumulated })
      }
    )

    const unlistenDone = await listen<{ message_id: string }>(
      'chat-done',
      (event) => {
        if (event.payload.message_id !== assistantId) return
        updateMessage(assistantId, { isStreaming: false })
        unlistenToken()
        unlistenDone()
        unlistenError()
      }
    )

    const unlistenError = await listen<{ message_id: string; error: string }>(
      'chat-error',
      (event) => {
        if (event.payload.message_id !== assistantId) return
        updateMessage(assistantId, {
          content: `Model unavailable: ${event.payload.error}\n\nPlace your fine-tuned model.gguf in the app data directory to enable AI responses.`,
          isStreaming: false,
        })
        unlistenToken()
        unlistenDone()
        unlistenError()
      }
    )

    cleanupRef.current.push(unlistenToken, unlistenDone, unlistenError)

    try {
      await invoke('send_chat_message', {
        message: text,
        messageId: assistantId,
        history,
      })
    } catch (err) {
      updateMessage(assistantId, {
        content: `Failed to send message: ${err}`,
        isStreaming: false,
      })
      unlistenToken()
      unlistenDone()
      unlistenError()
    }
  }, [messages, addMessage, updateMessage])

  const displayMessages = messages.length === 0
    ? [WELCOME_MESSAGE]
    : [WELCOME_MESSAGE, ...messages]

  return (
    <div className="flex flex-col h-full overflow-hidden bg-[var(--surface-base)]">
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-5 scroll-smooth [scrollbar-gutter:stable]"
      >
        <div className="max-w-3xl mx-auto pb-2">
          {displayMessages.map(msg => (
            <ChatBubble key={msg.id} message={msg} />
          ))}
        </div>
      </div>

      <div className="max-w-3xl w-full mx-auto px-6 pb-1 bg-[color-mix(in_srgb,var(--surface-raised)_40%,transparent)] border-t border-[var(--surface-border)]">
        <ChatInput onSend={handleSend} isStreaming={isStreaming} />
      </div>
    </div>
  )
}
