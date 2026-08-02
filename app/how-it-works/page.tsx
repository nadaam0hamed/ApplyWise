'use client'

import Link from 'next/link'
import { Navigation } from '@/components/navigation'
import { Upload, Zap, FileText, Send } from 'lucide-react'

export default function HowItWorksPage() {
  const steps = [
    {
      number: 1,
      icon: Upload,
      title: 'Upload Your Documents',
      description: 'Simply drag and drop your documents or click to browse. Supports PDF, DOCX, images and more formats.',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      number: 2,
      icon: Zap,
      title: 'AI Analysis',
      description: 'Our AI instantly analyzes your documents, identifies gaps, and generates insights about your application.',
      color: 'from-purple-500 to-pink-500',
    },
    {
      number: 3,
      icon: Send,
      title: 'Get Recommendations',
      description: 'Receive personalized recommendations and actionable next steps to strengthen your application.',
      color: 'from-orange-500 to-red-500',
    },
    {
      number: 4,
      icon: FileText,
      title: 'Track & Submit',
      description: 'Monitor your progress with our readiness score and get reminders to stay on track with deadlines.',
      color: 'from-green-500 to-emerald-500',
    },
  ]

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto space-y-16">
          {/* Header */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl sm:text-5xl font-bold text-foreground">How It Works</h1>
            <p className="text-xl text-muted-foreground">
              Four simple steps to a stronger application
            </p>
          </div>

          {/* Steps */}
          <div className="space-y-12">
            {steps.map((step, idx) => {
              const Icon = step.icon
              return (
                <div key={idx}>
                  <div className="flex gap-8 items-start">
                    {/* Step Number and Icon */}
                    <div className="flex flex-col items-center">
                      <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${step.color} flex items-center justify-center text-white font-bold text-2xl flex-shrink-0`}>
                        {step.number}
                      </div>
                      {idx < steps.length - 1 && (
                        <div className="w-1 h-20 bg-gradient-to-b from-secondary/60 to-secondary/20 my-2"></div>
                      )}
                    </div>

                    {/* Content */}
                    <div className="pt-2 pb-8">
                      <h3 className="text-2xl font-bold text-foreground mb-2">{step.title}</h3>
                      <p className="text-lg text-muted-foreground">{step.description}</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Features Highlight */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-16">
            <div className="glassmorphism rounded-xl p-8 border border-secondary/20">
              <h3 className="text-xl font-bold text-foreground mb-4">Why ApplyWise?</h3>
              <ul className="space-y-3">
                <li className="flex gap-3">
                  <span className="text-secondary">✓</span>
                  <span className="text-foreground">AI-powered analysis saves you hours</span>
                </li>
                <li className="flex gap-3">
                  <span className="text-secondary">✓</span>
                  <span className="text-foreground">Never miss important deadlines</span>
                </li>
                <li className="flex gap-3">
                  <span className="text-secondary">✓</span>
                  <span className="text-foreground">Get personalized recommendations</span>
                </li>
                <li className="flex gap-3">
                  <span className="text-secondary">✓</span>
                  <span className="text-foreground">24/7 AI assistant support</span>
                </li>
              </ul>
            </div>

            <div className="glassmorphism rounded-xl p-8 border border-secondary/20">
              <h3 className="text-xl font-bold text-foreground mb-4">Supported Formats</h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  <span className="text-foreground">PDF</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  <span className="text-foreground">DOCX</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  <span className="text-foreground">PNG</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  <span className="text-foreground">JPG</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  <span className="text-foreground">JPEG</span>
                </div>
              </div>
            </div>
          </div>

          {/* CTA */}
          <div className="text-center space-y-6">
            <h2 className="text-3xl font-bold text-foreground">Ready to get started?</h2>
            <Link
              href="/signup"
              className="inline-block px-8 py-3 bg-gradient-to-r from-primary to-secondary text-background rounded-lg font-semibold hover:shadow-lg hover:shadow-primary/20 transition"
            >
              Start Your Free Account
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}
