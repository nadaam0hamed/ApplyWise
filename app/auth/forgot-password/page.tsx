'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Navigation } from '@/components/navigation'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500))
      setSubmitted(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Navigation />
      <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-background via-background to-background">
        <div className="w-full max-w-md space-y-8">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-3xl font-bold text-foreground mb-2">Forgot Password?</h1>
            <p className="text-muted-foreground">No worries! We'll send you reset instructions.</p>
          </div>

          {/* Form */}
          {!submitted ? (
            <form onSubmit={handleSubmit} className="glassmorphism rounded-xl p-8 space-y-6">
              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg bg-input border border-border text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition"
                  placeholder="you@example.com"
                  required
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2 bg-gradient-to-r from-primary to-secondary text-background rounded-lg font-medium hover:shadow-lg hover:shadow-primary/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>

              {/* Back to Login */}
              <p className="text-center text-muted-foreground text-sm">
                <Link href="/login" className="text-primary hover:text-primary/80">
                  Back to login
                </Link>
              </p>
            </form>
          ) : (
            <div className="glassmorphism rounded-xl p-8 space-y-4 text-center">
              <div className="w-12 h-12 rounded-full bg-secondary/20 mx-auto flex items-center justify-center">
                <span className="text-2xl">✓</span>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground mb-2">Check your email</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  We've sent password reset instructions to {email}
                </p>
              </div>
              <Link
                href="/login"
                className="inline-block px-6 py-2 bg-gradient-to-r from-primary to-secondary text-background rounded-lg font-medium hover:shadow-lg hover:shadow-primary/20 transition-all"
              >
                Back to Login
              </Link>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
