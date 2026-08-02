'use client'

import { Upload, Zap, BarChart3, AlertCircle, Calendar, CheckCircle } from 'lucide-react'

export function HowItWorks() {
  const steps = [
    {
      icon: Upload,
      title: 'Upload Documents',
      description: 'Share your files securely',
    },
    {
      icon: Zap,
      title: 'AI Extracts Info',
      description: 'Smart analysis begins',
    },
    {
      icon: BarChart3,
      title: 'Requirement Check',
      description: 'Compare against standards',
    },
    {
      icon: AlertCircle,
      title: 'Missing Detection',
      description: 'Identify gaps instantly',
    },
    {
      icon: Calendar,
      title: 'Timeline Creation',
      description: 'Plan your submission',
    },
    {
      icon: CheckCircle,
      title: 'Ready for Submit',
      description: 'Application complete',
    },
  ]

  return (
    <section id="how-it-works" className="py-20 sm:py-32 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4">
            How It Works
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Simple steps to prepare your application with AI assistance
          </p>
        </div>

        {/* Workflow */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6 md:gap-4">
          {steps.map((step, index) => {
            const Icon = step.icon
            return (
              <div key={step.title} className="flex flex-col items-center">
                {/* Step Card */}
                <div className="flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 mb-4 border-2 border-primary/40 hover:border-primary/60 transition-colors">
                  <Icon className="w-8 h-8 text-primary" />
                </div>

                {/* Text */}
                <h3 className="font-semibold text-foreground text-center mb-1">
                  {step.title}
                </h3>
                <p className="text-sm text-muted-foreground text-center">
                  {step.description}
                </p>

                {/* Connector Arrow - Hidden on last item and mobile */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute left-1/2 transform translate-x-1/2 mt-20 mb-4">
                    <div className="w-0.5 h-16 bg-gradient-to-b from-primary/20 to-transparent"></div>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Desktop Connector Lines */}
        <svg className="hidden lg:block absolute inset-0 pointer-events-none w-full" style={{ height: '400px', marginTop: '-200px' }}>
          <defs>
            <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#2563EB" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.2" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </section>
  )
}
