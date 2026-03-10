'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Send, User, Bot, Sparkles, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { API_BASE } from '@/app/api/config'

export const dynamic = 'force-dynamic'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hi. I'm the reversing assistant. I can help with binary analysis, Ghidra workflows, or general RE questions. Pick a model in Settings (Ollama) and say what you need.",
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }
    setMessages((prev) => [...prev, userMsg])
    const currentInput = input
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: currentInput,
          history: messages.map((m) => ({ role: m.role, content: m.content }))
        })
      })
      const data = await res.json()
      const reply = data?.reply ?? "I couldn't process that. Is Ollama running and a model selected in Settings?"
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: reply,
        timestamp: new Date()
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (error) {
      console.error('Chat error:', error)
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "Backend or Ollama isn't reachable. Check Settings and run webapp from start-webapp.ps1.",
        timestamp: new Date()
      }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <MessageSquare className="w-7 h-7 text-primary" />
            Chat
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Local LLM (Ollama). Select model in Settings.
          </p>
        </div>
        <Link href="/settings">
          <Button variant="outline" size="sm">Settings</Button>
        </Link>
      </div>

      <div className="flex flex-col h-[calc(100vh-14rem)] border border-border bg-card/40 backdrop-blur rounded-xl overflow-hidden shadow-lg">
        <div className="p-4 border-b border-border bg-muted/30 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          <span className="text-sm font-medium">Ollama</span>
        </div>

        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                  msg.role === 'assistant'
                    ? 'bg-primary/10 text-primary'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <Bot className="w-4 h-4" />
                ) : (
                  <User className="w-4 h-4" />
                )}
              </div>
              <div
                className={`max-w-[85%] p-3 rounded-lg text-sm ${
                  msg.role === 'assistant'
                    ? 'bg-muted/50 rounded-tl-none'
                    : 'bg-primary text-primary-foreground rounded-tr-none'
                }`}
              >
                {msg.content}
                <div className={`text-xs mt-1 opacity-70 ${msg.role === 'user' ? 'text-right' : ''}`}>
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-primary animate-pulse" />
              </div>
              <div className="p-3 rounded-lg bg-muted/50 text-sm text-muted-foreground">
                Thinking...
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-border bg-muted/20">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              placeholder="Ask about binary analysis, Ghidra, or RE..."
              className="flex-1 min-h-[44px] max-h-32 px-4 py-2 rounded-lg border border-input bg-background text-sm resize-y focus:outline-none focus:ring-2 focus:ring-ring"
              rows={1}
              disabled={loading}
            />
            <Button onClick={handleSend} disabled={loading || !input.trim()} size="icon" className="shrink-0 h-11 w-11">
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      <div className="mt-4 flex gap-4">
        <Link href="/">
          <Button variant="outline" size="sm">Home</Button>
        </Link>
        <Link href="/settings">
          <Button variant="outline" size="sm">Ollama model in Settings</Button>
        </Link>
      </div>
    </div>
  )
}
