import { createFileRoute } from '@tanstack/react-router'
import { MessageSquare, Send, Bot, User } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

export const Route = createFileRoute('/study')({
  component: StudyChatPage,
})

interface Message {
  role: 'user' | 'assistant'
  content: string
}

function StudyChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/chat/study', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ input: input }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer || 'I apologize, but I could not process your request.',
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-base-100 flex flex-col">
      {/* Header */}
      <div className="bg-base-200 border-b border-base-300 py-6">
        <div className="container mx-auto px-4">
          <div className="flex items-center gap-4">
            <div className="avatar placeholder">
              <div className="bg-linear-to-br from-accent to-secondary text-accent-content w-12 rounded-full">
                <Bot className="w-6 h-6" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-base-content">AI Study Assistant</h1>
              <p className="text-base-content/70">
                Ask me anything about your flashcards
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto py-8 bg-base-100">
        <div className="container mx-auto px-4 max-w-4xl">
          {messages.length === 0 ? (
            <div className="text-center py-16">
              <MessageSquare className="w-16 h-16 text-accent/50 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-base-content mb-2">
                Start a Conversation
              </h2>
              <p className="text-base-content/70">
                Ask questions about your flashcards and I'll help you study!
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`chat ${message.role === 'user' ? 'chat-end' : 'chat-start'}`}
                >
                  <div className="chat-image avatar">
                    <div className="w-10 rounded-full">
                      {message.role === 'user' ? (
                        <div className="bg-primary w-full h-full flex items-center justify-center rounded-full">
                          <User className="w-5 h-5 text-primary-content" />
                        </div>
                      ) : (
                        <div className="bg-linear-to-br from-accent to-secondary w-full h-full flex items-center justify-center rounded-full">
                          <Bot className="w-5 h-5 text-accent-content" />
                        </div>
                      )}
                    </div>
                  </div>
                  <div
                    className={`chat-bubble ${
                      message.role === 'user'
                        ? 'chat-bubble-primary'
                        : 'chat-bubble-accent'
                    }`}
                  >
                    {message.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="chat chat-start">
                  <div className="chat-image avatar">
                    <div className="w-10 rounded-full">
                      <div className="bg-linear-to-br from-accent to-secondary w-full h-full flex items-center justify-center rounded-full">
                        <Bot className="w-5 h-5 text-accent-content" />
                      </div>
                    </div>
                  </div>
                  <div className="chat-bubble chat-bubble-accent">
                    <span className="loading loading-dots loading-sm"></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-base-200 border-t border-base-300 py-4">
        <div className="container mx-auto px-4 max-w-4xl">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question..."
              className="input input-bordered input-accent flex-1"
              disabled={isLoading}
            />
            <button
              type="submit"
              className="btn btn-accent"
              disabled={!input.trim() || isLoading}
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}