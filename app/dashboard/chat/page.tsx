'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { Navigation } from '@/components/navigation'
import { Send, Paperclip, ChevronDown } from 'lucide-react'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I am your ApplyWise AI assistant. I can help you with your application process. Ask me anything about your documents, timeline, or recommendations.',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const suggestedPrompts = [
    'What documents do I still need?',
    'Help me write my Statement of Purpose',
    'When is my application deadline?',
    'What is my current readiness score?',
  ]

  const mockResponses: { [key: string]: string } = {
    'documents': 'Based on your uploaded files, you still need: Letter of Recommendation, Statement of Purpose, and GRE Scores. I recommend prioritizing the SOP and recommendation letters as they are due soon.',
    'sop': 'Your Statement of Purpose should be 500-750 words, addressing: (1) Your academic background, (2) Why this program, (3) Your career goals, (4) How this program helps you achieve them. Would you like me to help outline it?',
    'deadline': 'Your application deadline is July 25, 2024 - that is 3 days away. I recommend submitting your documents as soon as possible.',
    'readiness': 'Your current readiness score is 78%. You have completed most sections, but need to submit 2 more critical documents to increase it to 95%.',
    'default': 'That\'s a great question! Based on your application profile, I recommend focusing on completing your Statement of Purpose and gathering your recommendation letters. These are the most critical missing pieces right now. Is there anything specific about these documents you\'d like help with?',
  }

  const handleSendMessage = async (text: string = input) => {
    if (!text.trim()) return

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: text,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    // Simulate AI response delay
    await new Promise(resolve => setTimeout(resolve, 800))

    // Determine response based on keyword
    let response = mockResponses.default
    const lowerText = text.toLowerCase()

    if (lowerText.includes('document') || lowerText.includes('missing')) {
      response = mockResponses.documents
    } else if (lowerText.includes('sop') || lowerText.includes('statement')) {
      response = mockResponses.sop
    } else if (lowerText.includes('deadline') || lowerText.includes('when')) {
      response = mockResponses.deadline
    } else if (lowerText.includes('readiness') || lowerText.includes('score')) {
      response = mockResponses.readiness
    }

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: response,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, assistantMessage])
    setIsTyping(false)
  }

  const handleSuggestedPrompt = (prompt: string) => {
    handleSendMessage(prompt)
  }

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-120px)]">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-2xl font-bold text-foreground">AI Assistant</h1>
              <Link
                href="/dashboard"
                className="text-sm text-muted-foreground hover:text-foreground transition"
              >
                ← Back to Dashboard
              </Link>
            </div>
            <p className="text-muted-foreground">Ask me anything about your application process</p>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto mb-6 space-y-4 pr-2">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xl lg:max-w-2xl rounded-lg px-4 py-3 ${
                    message.type === 'user'
                      ? 'bg-gradient-to-r from-primary to-secondary text-background'
                      : 'glassmorphism text-foreground border border-secondary/20'
                  }`}
                >
                  <p className="text-sm leading-relaxed">{message.content}</p>
                  <p className={`text-xs mt-1 ${
                    message.type === 'user'
                      ? 'text-background/70'
                      : 'text-muted-foreground'
                  }`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="glassmorphism rounded-lg px-4 py-3 border border-secondary/20">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 rounded-full bg-secondary animate-bounce"></div>
                    <div className="w-2 h-2 rounded-full bg-secondary animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 rounded-full bg-secondary animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Prompts */}
          {messages.length === 1 && (
            <div className="mb-6 space-y-3">
              <p className="text-sm text-muted-foreground mb-3">Try asking:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {suggestedPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSuggestedPrompt(prompt)}
                    className="p-3 rounded-lg border border-secondary/30 text-foreground hover:bg-secondary/10 hover:border-secondary/50 transition text-left text-sm"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="glassmorphism rounded-xl p-4 border border-secondary/20">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSendMessage()
                  }
                }}
                placeholder="Ask me about your application..."
                className="flex-1 bg-input border border-border rounded-lg px-4 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={!input.trim() || isTyping}
                className="p-2 rounded-lg bg-gradient-to-r from-primary to-secondary text-background hover:shadow-lg hover:shadow-primary/20 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send size={20} />
              </button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">Press Enter to send message</p>
          </div>
        </div>
      </div>
    </>
  )
}
